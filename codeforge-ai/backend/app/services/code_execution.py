"""Code execution service — isolated subprocess sandbox.

User code never runs inside the FastAPI process: each test case is executed
in a fresh, time-limited subprocess (``python -I`` or ``node``) driven by a
runner script. Inputs are parsed in the parent process so Python and
JavaScript share one parsing implementation.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("execution")

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
PY_RUNNER = os.path.join(SERVICE_DIR, "runner_python.py")
NODE_RUNNER = os.path.join(SERVICE_DIR, "runner_node.mjs")

SUPPORTED_LANGUAGES = ("python", "javascript", "java", "cpp", "c")
ASSIGN_RE = re.compile(r'(?<![\w.\'"])([A-Za-z_]\w*)\s*=\s*')
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class CodeExecutionService:
    """Runs user code against test cases in isolated subprocesses."""

    def __init__(self):
        self.timeout_ms = settings.code_execution_timeout * 1000
        self.memory_limit_mb = settings.code_execution_memory_limit

    # ── capability probing ────────────────────────────────────────────────
    @staticmethod
    def available_languages() -> List[Dict[str, Any]]:
        """Languages the executor can actually run on this machine."""
        langs = [
            {
                "id": "python",
                "label": "Python 3",
                "version": sys.version.split()[0],
                "available": True,
            }
        ]
        node = shutil.which("node")
        if node:
            ver = ""
            try:
                out = subprocess.run(
                    [node, "--version"], capture_output=True, text=True, timeout=5,
                    creationflags=_CREATE_NO_WINDOW,
                )
                ver = (out.stdout or out.stderr).strip()
            except Exception:
                ver = ""
            langs.append(
                {"id": "javascript", "label": "JavaScript", "version": ver, "available": True}
            )
        for lang, cmd in (("java", ["javac", "-version"]), ("cpp", ["g++", "--version"]), ("c", ["gcc", "--version"])):
            exe = shutil.which(cmd[0])
            langs.append(
                {"id": lang, "label": lang.upper(), "version": "", "available": bool(exe)}
            )
        return langs

    @staticmethod
    def _runner_for(language: str) -> Optional[str]:
        if language == "python" and os.path.exists(PY_RUNNER):
            return PY_RUNNER
        if language == "javascript" and os.path.exists(NODE_RUNNER) and shutil.which("node"):
            return NODE_RUNNER
        return None

    # ── validation ────────────────────────────────────────────────────────
    def validate_code(self, code: str, language: str) -> Tuple[bool, Optional[str]]:
        if not code or len(code.strip()) < 5:
            return False, "Code is empty or too short"
        if len(code) > 100000:
            return False, "Code exceeds maximum length (100,000 characters)"
        if language not in SUPPORTED_LANGUAGES:
            return False, f"Unsupported language: {language}"
        if self._runner_for(language) is None:
            return (
                False,
                f"No runtime available for '{language}' on this server. "
                f"Available: {', '.join(l['id'] for l in self.available_languages() if l['available'])}.",
            )
        if language == "python":
            for pattern in ("import os", "import subprocess", "import socket", "__import__"):
                if pattern in code:
                    logger.warning("Potentially dangerous pattern", pattern=pattern)
        return True, None

    # ── input parsing (shared by every language) ──────────────────────────
    @staticmethod
    def _literal(raw: str) -> Any:
        text = raw.strip()
        if not text:
            return ""
        try:
            return ast.literal_eval(text)
        except Exception:
            pass
        # test data sometimes uses JSON-style null
        try:
            return ast.literal_eval(re.sub(r"\bnull\b", "None", text))
        except Exception:
            pass
        return text

    @staticmethod
    def parse_input(input_data: str) -> Tuple[List[Any], Dict[str, Any]]:
        """Parse a test-case input into positional args + keyword args.

        Handles:
          - ``nums = [2,7,11,15], target = 9``  (multi assignment, one line)
          - ``numCourses = 2`` / multi-line assignments
          - bare literals: ``[1,2,3]``, ``121``, ``abcabcbb``
        """
        text = (input_data or "").strip()
        if not text:
            return [], {}

        matches = list(ASSIGN_RE.finditer(text))
        if matches:
            # only treat as assignments when every segment parses as name = value
            kwargs: Dict[str, Any] = {}
            for i, m in enumerate(matches):
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                raw = text[start:end].strip()
                if raw.endswith(","):
                    raw = raw[:-1].strip()
                kwargs[m.group(1)] = CodeExecutionService._literal(raw)
            return [], kwargs

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) > 1:
            return [CodeExecutionService._literal(line) for line in lines], {}
        return [CodeExecutionService._literal(text)], {}

    # ── output comparison ─────────────────────────────────────────────────
    @staticmethod
    def _normalize_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        return value

    @staticmethod
    def _deep_sort(value):
        if isinstance(value, list):
            if all(isinstance(x, list) for x in value):
                return sorted(
                    [CodeExecutionService._deep_sort(x) for x in value],
                    key=lambda x: json.dumps(x, sort_keys=True),
                )
            if all(isinstance(x, (list, tuple)) for x in value):
                return sorted(value, key=lambda x: json.dumps(list(x), sort_keys=True))
            if value and all(isinstance(x, (str, int, float, bool)) for x in value):
                # grouped results: element order inside a group is not meaningful
                return sorted(value, key=lambda x: json.dumps(x))
            return [
                CodeExecutionService._deep_sort(x) if isinstance(x, (list, tuple)) else x
                for x in value
            ]
        return value

    def _compare_output(self, actual: str, expected: str) -> bool:
        a = (actual or "").strip()
        e = (expected or "").strip()
        if a == e:
            return True
        # empty result vs empty list ("", "[]", "null") are the same answer
        empties = ("", "[]", "null", "None")
        if a in empties and e in empties:
            return True
        if a.lower() == e.lower() and a.lower() in ("true", "false"):
            return True
        if self._normalize_quotes(a) == e or a == self._normalize_quotes(e):
            return True
        if a.replace(" ", "") == e.replace(" ", ""):
            return True

        try:
            av = ast.literal_eval(a)
            ev = ast.literal_eval(e)
        except Exception:
            av = ev = None
        if av is None and ev is None:
            # JSON-style literals: null/true/false are not valid Python
            try:
                av = ast.literal_eval(
                    re.sub(r"\btrue\b", "True",
                           re.sub(r"\bfalse\b", "False",
                                  re.sub(r"\bnull\b", "None", a)))
                )
                ev = ast.literal_eval(
                    re.sub(r"\btrue\b", "True",
                           re.sub(r"\bfalse\b", "False",
                                  re.sub(r"\bnull\b", "None", e)))
                )
            except Exception:
                av = ev = None
        if av is not None and ev is not None:
            if av == ev:
                return True
            if isinstance(av, list) and isinstance(ev, list):
                # tolerate ordering differences for grouped/nested results
                if all(isinstance(x, list) for x in av) and all(
                    isinstance(x, list) for x in ev
                ):
                    if self._deep_sort(av) == self._deep_sort(ev):
                        return True
                try:
                    import json as _json
                    if _json.dumps(av) == _json.dumps(ev):
                        return True
                except Exception:
                    pass
        return False

    # ── execution ─────────────────────────────────────────────────────────
    async def execute(
        self,
        code: str,
        language: str,
        test_cases: List[dict] = None,
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        valid, error = self.validate_code(code, language)
        if not valid:
            return self._empty_result("compilation_error", error)
        return await asyncio.to_thread(
            self._execute_sync, code, language, test_cases or [], timeout_ms
        )

    def _execute_sync(
        self,
        code: str,
        language: str,
        test_cases: List[dict],
        timeout_ms: Optional[int],
    ) -> Dict[str, Any]:
        runner = self._runner_for(language)
        per_test_timeout = (timeout_ms or self.timeout_ms) / 1000.0
        param_hints = self._param_hints(test_cases)

        results: List[Dict[str, Any]] = []
        compile_error = None
        runtime_error = None
        timeout_hit = False
        memory_hit = False
        total_runtime = 0
        total_memory = 0
        stdout_tail = ""

        for tc in test_cases:
            args, kwargs = self.parse_input(tc.get("input", ""))
            job = {
                "code": code,
                "args": args,
                "kwargs": kwargs,
                "params": param_hints,
                "memory_limit_kb": self.memory_limit_mb * 1024,
            }
            outcome = self._run_job(runner, language, job, per_test_timeout)

            actual = outcome.get("actual", "")
            passed = False
            error_kind = outcome.get("kind", "")

            if outcome.get("ok"):
                expected = str(tc.get("output", ""))
                passed = self._compare_output(actual, expected)
                if not passed:
                    for alt in outcome.get("alternates") or []:
                        if self._compare_output(str(alt), expected):
                            actual = str(alt)
                            passed = True
                            break
            else:
                if error_kind == "compile" and compile_error is None:
                    compile_error = outcome.get("error") or "Compilation failed"
                elif error_kind == "timeout":
                    timeout_hit = True
                elif error_kind == "memory":
                    memory_hit = True
                elif runtime_error is None and outcome.get("error"):
                    runtime_error = outcome.get("error")
                    stdout_tail = outcome.get("stdout", "") or stdout_tail

            total_runtime = max(total_runtime, int(outcome.get("runtime_ms") or 0))
            total_memory = max(total_memory, int(outcome.get("memory_kb") or 0))

            results.append(
                {
                    "test_number": len(results) + 1,
                    "input_data": tc.get("input", ""),
                    "expected_output": str(tc.get("output", "")),
                    "actual_output": actual,
                    "passed": passed,
                    "is_public": bool(tc.get("is_public", True)),
                    "error": outcome.get("error") or "",
                }
            )

            if compile_error is not None:
                break

        passed_count = sum(1 for r in results if r["passed"])
        if compile_error is not None:
            status = "compilation_error"
            message = compile_error
        elif timeout_hit:
            status = "time_limit"
            message = f"Time limit exceeded ({per_test_timeout:g}s per test case)"
        elif memory_hit:
            status = "memory_limit"
            message = f"Memory limit exceeded ({self.memory_limit_mb} MB)"
        elif runtime_error is not None:
            status = "runtime_error"
            message = runtime_error
        elif not results:
            status = "wrong_answer"
            message = "No test cases to run"
        elif passed_count == len(results):
            status = "accepted"
            message = None
        else:
            status = "wrong_answer"
            message = None

        logger.info(
            "execution finished",
            language=language,
            status=status,
            passed=f"{passed_count}/{len(results)}",
            runtime_ms=total_runtime,
        )
        return {
            "status": status,
            "runtime_ms": total_runtime,
            "memory_kb": total_memory,
            "stdout": stdout_tail,
            "stderr": "",
            "error_message": message,
            "test_results": results,
            "total_passed": passed_count,
            "total_failed": len(results) - passed_count,
        }

    @staticmethod
    def _param_hints(test_cases: List[dict]) -> List[str]:
        for tc in test_cases:
            _, kwargs = CodeExecutionService.parse_input(tc.get("input", ""))
            if kwargs:
                return list(kwargs.keys())
        return []

    def _run_job(
        self, runner: str, language: str, job: dict, timeout_s: float
    ) -> Dict[str, Any]:
        node = shutil.which("node") if language == "javascript" else None
        if language == "python":
            cmd = [sys.executable, "-I", runner]
        elif language == "javascript":
            if not node:
                return {"ok": False, "kind": "compile", "error": "Node.js runtime not available"}
            cmd = [node, runner]
        else:
            return {
                "ok": False,
                "kind": "compile",
                "error": f"Language '{language}' runtime is not installed on this server",
            }

        tmpdir = tempfile.mkdtemp(prefix="cf_exec_")
        job_path = os.path.join(tmpdir, "job.json")
        try:
            with open(job_path, "w", encoding="utf-8") as fh:
                json.dump(job, fh)
            started = time.perf_counter()
            proc = subprocess.run(
                cmd + [job_path],
                capture_output=True,
                text=True,
                timeout=max(timeout_s, 1.0),
                cwd=tmpdir,
                creationflags=_CREATE_NO_WINDOW,
            )
            elapsed = int((time.perf_counter() - started) * 1000)
            payload = self._parse_payload(proc.stdout)
            if payload is None:
                err = (proc.stderr or "").strip().splitlines()
                tail = err[-1] if err else "Runner produced no output"
                return {
                    "ok": False,
                    "kind": "runtime",
                    "error": f"Internal execution failure: {tail[:300]}",
                    "actual": "",
                    "runtime_ms": elapsed,
                    "memory_kb": 0,
                    "stdout": "",
                }
            payload.setdefault("runtime_ms", elapsed)
            mem = int(payload.get("memory_kb") or 0)
            if mem > self.memory_limit_mb * 1024 and payload.get("ok"):
                return {
                    "ok": False,
                    "kind": "memory",
                    "error": f"Memory limit exceeded ({self.memory_limit_mb} MB)",
                    "actual": "",
                    "runtime_ms": payload.get("runtime_ms", elapsed),
                    "memory_kb": mem,
                    "stdout": payload.get("stdout", ""),
                }
            return payload
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "kind": "timeout",
                "error": "Time limit exceeded",
                "actual": "",
                "runtime_ms": int(timeout_s * 1000),
                "memory_kb": 0,
                "stdout": "",
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("execution failure", error=str(exc))
            return {
                "ok": False,
                "kind": "runtime",
                "error": f"Execution engine error: {exc}",
                "actual": "",
                "runtime_ms": 0,
                "memory_kb": 0,
                "stdout": "",
            }
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @staticmethod
    def _parse_payload(stdout: str) -> Optional[Dict[str, Any]]:
        text = (stdout or "").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # runner prints exactly one JSON object; fall back to the last line
            for line in reversed(text.splitlines()):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return None

    @staticmethod
    def _empty_result(status: str, message: str) -> Dict[str, Any]:
        return {
            "status": status,
            "runtime_ms": 0,
            "memory_kb": 0,
            "stdout": "",
            "stderr": "",
            "error_message": message,
            "test_results": [],
            "total_passed": 0,
            "total_failed": 0,
        }


execution_service: Optional[CodeExecutionService] = None


def get_execution_service() -> CodeExecutionService:
    global execution_service
    if execution_service is None:
        execution_service = CodeExecutionService()
    return execution_service
