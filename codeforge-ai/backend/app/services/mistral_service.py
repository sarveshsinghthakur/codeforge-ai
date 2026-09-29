"""Mistral AI service abstraction."""
import json
from typing import AsyncIterator, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger("mistral")

# ── live .env reload ─────────────────────────────────────────────────────────
# uvicorn --reload only watches *.py, so editing backend/.env never restarts
# the process. Re-read MISTRAL_* whenever the file's mtime changes.
import os  # noqa: E402
from pathlib import Path  # noqa: E402

_ENV_PATH = Path(os.environ.get("MISTRAL_ENV_PATH", Path(__file__).resolve().parents[2] / ".env"))
_env_cache = {"mtime": None, "key": None, "model": None, "fallbacks": []}


def _reload_env_if_changed() -> bool:
    """Re-parse MISTRAL_API_KEY/MODEL/FALLBACKS from .env if it changed. True if reloaded."""
    try:
        mtime = _ENV_PATH.stat().st_mtime
    except OSError:
        return False
    if _env_cache["mtime"] == mtime:
        return False
    _env_cache["mtime"] = mtime
    key, model, fallbacks = "", "", ""
    try:
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, val = line.partition("=")
            name = name.strip()
            val = val.strip().strip('"').strip("'")
            if name == "MISTRAL_API_KEY":
                key = val
            elif name == "MISTRAL_MODEL":
                model = val
            elif name == "MISTRAL_FALLBACK_MODELS":
                fallbacks = val
    except OSError:
        pass
    _env_cache["key"] = key
    _env_cache["model"] = model
    _env_cache["fallbacks"] = [m.strip() for m in fallbacks.split(",") if m.strip()]
    return True


class MistralError(Exception):
    """Safe, user-presentable AI failure (never leaks keys/stack traces)."""

    def __init__(self, kind: str, message: str, status_code: int = 502, retryable: bool = False):
        self.kind = kind
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(f"{kind}: {message}")

    def payload(self) -> dict:
        return {"error": self.kind, "message": self.message, "retryable": self.retryable}


class MistralService:
    """AI service abstraction for Mistral. Swappable provider."""

    def __init__(self, api_key: str = None, model: str = None):
        _reload_env_if_changed()
        self._explicit_key = api_key
        self.api_key = api_key or _env_cache["key"] or settings.mistral_api_key
        self.model = model or _env_cache["model"] or settings.mistral_model or "codestral-2508"
        self.fallback_models = [m for m in _env_cache.get("fallbacks", []) if m != self.model]
        self.base_url = "https://api.mistral.ai/v1"
        self.client: Optional[httpx.AsyncClient] = None
        self._client_key: Optional[str] = None

    def _models_to_try(self) -> list:
        """Primary model first, then configured fallbacks (deduped)."""
        out = []
        for m in [self.model] + list(self.fallback_models):
            if m and m not in out:
                out.append(m)
        return out or [self.model]

    def _sync_env(self):
        """Adopt a new .env key without restarting the process."""
        if not _reload_env_if_changed() or self._explicit_key is not None:
            return
        if _env_cache["key"] and _env_cache["key"] != self.api_key:
            logger.info("mistral_api_key_reloaded")
            self.api_key = _env_cache["key"]
            self._client_key = None  # force client rebuild with new header
        if _env_cache["model"] and _env_cache["model"] != self.model:
            self.model = _env_cache["model"]
        self.fallback_models = [m for m in _env_cache.get("fallbacks", []) if m != self.model]

    async def _get_client(self) -> httpx.AsyncClient:
        self._sync_env()
        if self.client is None or self.client.is_closed or self._client_key != self.api_key:
            if self.client is not None and not self.client.is_closed:
                await self.client.aclose()
            self._client_key = self.api_key
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
        return self.client

    async def close(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()

    # ── error mapping ──────────────────────────────────────────────────────
    def _require_key(self):
        self._sync_env()
        if not self.api_key:
            raise MistralError(
                "not_configured",
                "AI assistant is not configured. Add MISTRAL_API_KEY to backend/.env and restart the server.",
                status_code=503,
                retryable=False,
            )

    @staticmethod
    def _map_status(status_code: int) -> MistralError:
        if status_code in (401, 403):
            return MistralError(
                "auth",
                "AI service rejected the API key. Replace MISTRAL_API_KEY in backend/.env with a valid key.",
                status_code=502,
                retryable=False,
            )
        if status_code == 429:
            return MistralError(
                "rate_limit",
                "AI service is rate limited right now. Wait a moment and try again.",
                status_code=429,
                retryable=True,
            )
        if status_code >= 500:
            return MistralError(
                "upstream",
                "AI service is temporarily unavailable. Please try again shortly.",
                status_code=502,
                retryable=True,
            )
        return MistralError(
            "request",
            "AI service rejected the request.",
            status_code=502,
            retryable=False,
        )

    async def _post_chat(self, payload: dict, allow_fallback: bool = True) -> dict:
        self._require_key()
        client = await self._get_client()
        models = self._models_to_try() if allow_fallback else [payload.get("model") or self.model]
        last_error: Optional[MistralError] = None
        for i, mdl in enumerate(models):
            payload = {**payload, "model": mdl}
            try:
                response = await client.post("/chat/completions", json=payload)
            except httpx.TimeoutException:
                raise MistralError(
                    "timeout",
                    "AI request timed out. Please try again.",
                    status_code=504,
                    retryable=True,
                )
            except httpx.HTTPError:
                raise MistralError(
                    "network",
                    "Could not reach the AI service. Check the server's network connection.",
                    status_code=502,
                    retryable=True,
                )
            if response.status_code in (403, 429) and i < len(models) - 1:
                # model unavailable on this tier / rate limited -> try next model
                last_error = self._map_status(response.status_code)
                logger.warning("mistral_model_fallback", extra={"model": mdl, "status": response.status_code})
                continue
            if response.status_code >= 400:
                raise self._map_status(response.status_code)
            try:
                data = response.json()
            except ValueError:
                raise MistralError(
                    "invalid_response",
                    "AI service returned an unreadable response.",
                    status_code=502,
                    retryable=True,
                )
            if not data.get("choices"):
                raise MistralError(
                    "empty_response",
                    "AI service returned an empty response. Please try again.",
                    status_code=502,
                    retryable=True,
                )
            if mdl != self.model:
                logger.info("mistral_fallback_used", extra={"model": mdl})
            return data
        raise last_error or MistralError(
            "rate_limit",
            "AI service is rate limited right now. Wait a moment and try again.",
            status_code=429,
            retryable=True,
        )

    async def chat(
        self,
        messages: list,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> tuple[str, int]:
        """Non-streaming chat. Returns (text, tokens_used)."""
        data = await self._post_chat({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        text = data["choices"][0]["message"].get("content") or ""
        tokens = data.get("usage", {}).get("total_tokens", 0)
        if not text.strip():
            raise MistralError(
                "empty_response",
                "AI service returned an empty response. Please try again.",
                status_code=502,
                retryable=True,
            )
        return text, tokens

    async def chat_stream(
        self,
        messages: list,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Yields text deltas from a streaming completion."""
        self._require_key()
        client = await self._get_client()
        models = self._models_to_try()
        last_error: Optional[MistralError] = None
        for i, mdl in enumerate(models):
            payload = {
                "model": mdl,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }
            try:
                async with client.stream("POST", "/chat/completions", json=payload) as resp:
                    if resp.status_code >= 400:
                        await resp.aread()
                        if resp.status_code in (403, 429) and i < len(models) - 1:
                            last_error = self._map_status(resp.status_code)
                            logger.warning(
                                "mistral_model_fallback",
                                extra={"model": mdl, "status": resp.status_code},
                            )
                            continue
                        raise self._map_status(resp.status_code)
                    if mdl != self.model:
                        logger.info("mistral_fallback_used", extra={"model": mdl})
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = (choices[0].get("delta") or {}).get("content")
                        if delta:
                            yield delta
                    return
            except MistralError:
                raise
            except httpx.TimeoutException:
                raise MistralError(
                    "timeout", "AI request timed out. Please try again.", status_code=504, retryable=True
                )
            except httpx.HTTPError:
                raise MistralError(
                    "network",
                    "Could not reach the AI service. Check the server's network connection.",
                    status_code=502,
                    retryable=True,
                )
        raise last_error or MistralError(
            "rate_limit",
            "AI service is rate limited right now. Wait a moment and try again.",
            status_code=429,
            retryable=True,
        )

    async def generate_text(
        self,
        prompt: str,
        system_message: str = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if prompt and prompt.strip():
            messages.append({"role": "user", "content": prompt})
        else:
            # some callers put everything in the system message
            messages.append({"role": "user", "content": system_message or "Continue."})
        text, _ = await self.chat(messages, max_tokens=max_tokens, temperature=temperature)
        return text

    async def generate_json(
        self,
        prompt: str,
        schema: dict = None,
        system_message: str = None,
    ) -> dict:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        json_prompt = prompt + "\n\nReturn ONLY valid JSON. No markdown, no explanations."
        messages.append({"role": "user", "content": json_prompt})

        data = await self._post_chat({
            "model": self.model,
            "messages": messages,
            "max_tokens": 8000,
            "temperature": 0.2,
        })
        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.rindex("```")
                return json.loads(content[start:end].strip())
            elif "```" in content:
                start = content.index("```") + 3
                end = content.rindex("```")
                return json.loads(content[start:end].strip())
            raise MistralError(
                "invalid_response",
                "AI service returned malformed JSON.",
                status_code=502,
                retryable=True,
            )

    async def generate_problem(self, prompt: str) -> dict:
        """Generate a complete problem from a natural language prompt."""
        system = """You are an expert competitive programming problem creator.
Generate COMPLETELY ORIGINAL problems. Never copy from LeetCode, Codeforces, HackerRank, or any other platform.

Return a JSON object with this exact structure:
{
  "title": "A unique, descriptive title",
  "slug": "url-friendly-slug-with-hyphens",
  "difficulty": "easy" | "medium" | "hard",
  "description": "Problem statement in markdown",
  "constraints": ["Constraint 1", "Constraint 2", ...],
  "examples": [
    {"input": "example input here", "output": "expected output", "explanation": "why this is the answer"},
    {"input": "another example", "output": "expected output", "explanation": "explanation"}
  ],
  "topics": ["Array", "Two Pointers", ...],
  "hints": ["Hint 1: ...", "Hint 2: ...", "Hint 3: ..."],
  "follow_up": "Follow-up question or null",
  "starter_code": {
    "python": "def solution(...):\n    pass\n",
    "javascript": "function solution(...)\n{\n    \n}",
    "java": "class Solution {\n    public ... \n}",
    "cpp": "class Solution {\npublic:\n    ... \n};",
    "c": "int solution(...)\n{\n    return 0;\n}"
  },
  "solution_explanation": "Explanation of the approach",
  "complexity": {"time": "O(n log n)", "space": "O(n)"},
  "test_cases": [
    {"input": "input string", "output": "expected output string"}
  ],
  "reference_solution": "python code for reference solution",
  "company": "company name or null"
}

RULES:
1. Title must be unique, not a known problem name
2. At least 2 examples with explanations
3. At least 2 hints
4. Starter code for ALL 5 languages
5. Include at least 5 test cases
6. Reference solution must be correct Python code
7. Topics should be 1-4 relevant topics
8. Description in markdown format
9. Constraints must specify input size limits
10. Slug must be lowercase hyphenated"""

        return await self.generate_json(prompt, system_message=system)

    async def generate_test_cases(self, problem: dict, count: int = 10) -> list:
        """Generate test cases for a problem."""
        system = """You are a test case generator.
Generate diverse test cases covering edge cases.
Return ONLY a JSON array of objects with "input" and "output" fields."""

        prompt = f"""Generate {count} test cases for this problem:

Title: {problem.get('title', '')}
Difficulty: {problem.get('difficulty', '')}
Description:
{problem.get('description', '')}

Constraints:
{chr(10).join(f"- {c}" for c in problem.get('constraints', []))}

Examples:
{chr(10).join(f"Input: {e.get('input','')}\nOutput: {e.get('output','')}" for e in problem.get('examples', []))}

Generate test cases covering:
- Empty input
- Minimum constraints
- Maximum constraints
- Duplicates
- Sorted input
- Reverse sorted
- Single element
- All equal values
- Negative values
- Large values
- Boundary cases

Return ONLY a JSON array."""

        return await self.generate_json(prompt, system_message=system)

    async def analyze_code(
        self,
        code: str,
        language: str,
        problem_description: str = None,
    ) -> dict:
        """Analyze code and return structured feedback."""
        system = """You are a code reviewer. Analyze the code for:
1. Correctness
2. Time and space complexity
3. Potential bugs
4. Edge cases
5. Optimizations

Return a JSON object:
{
  "analysis": "Overall analysis text",
  "suggestions": ["suggestion 1", "suggestion 2"],
  "complexity": {"time": "O(n)", "space": "O(1)", "explanation": "why"},
  "bugs": ["bug 1", "bug 2"],
  "edge_cases": ["edge case 1", "edge case 2"]
}"""

        prompt = f"""Language: {language}
{"Problem: " + problem_description if problem_description else ""}

Code:
{code}

Provide analysis."""

        try:
            return await self.generate_json(prompt, system_message=system)
        except Exception:
            text = await self.generate_text(prompt, system_message=system, max_tokens=2000)
            return {
                "analysis": text,
                "suggestions": [],
                "complexity": {"time": "", "space": "", "explanation": ""},
                "bugs": [],
                "edge_cases": [],
            }

    async def generate_hints(self, problem: dict, code: str = None, level: int = 1) -> str:
        """Generate progressive hints."""
        levels = {
            1: "Give a very subtle hint about the general approach. Do NOT reveal the solution.",
            2: "Give a more specific hint about the algorithm or approach. Still do NOT give away the solution.",
            3: "Give a detailed hint that nearly reveals the approach but still requires implementation.",
        }

        system = f"""You are a coding assistant giving progressive hints.

{levels[level]}

Problem:
{problem.get('description', '')}

Difficulty: {problem.get('difficulty', '')}
Topics: {', '.join(problem.get('topics', []))}
Constraints:
{chr(10).join(f'- {c}' for c in problem.get('constraints', []))}

{('User code:\n' + code) if code else ''}

Return ONLY the hint text. Do NOT include the full solution.
Do NOT include preamble like "Here's a hint:" — just the hint itself."""

        return await self.generate_text(system_message=system, prompt="")


mistral_service: Optional[MistralService] = None


def get_mistral_service() -> MistralService:
    global mistral_service
    if mistral_service is None:
        mistral_service = MistralService()
    return mistral_service
