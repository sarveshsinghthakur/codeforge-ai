"""AI copilot API — powers the side panel and the workspace AI tab.

One service, two transports:
  POST /api/ai/copilot         -> JSON reply
  POST /api/ai/copilot/stream  -> SSE stream of {type: delta|done|error}

Errors always come back as a structured, secret-free body:
  {"error": "<kind>", "message": "<human text>", "retryable": bool}
"""
from __future__ import annotations

import json
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.config import settings
from app.core.security import require_user
from app.models.ai import AIConversation, AIMessage
from app.models.problem import Problem, ProblemStatus
from app.models.user import User
from app.schemas.ai import CopilotRequest, CopilotResponse
from app.services.mistral_service import MistralError, get_mistral_service

router = APIRouter()

QUICK_ACTIONS = [
    {"id": "explain_problem", "label": "Explain Problem", "description": "Plain-English walkthrough of the statement"},
    {"id": "hint", "label": "Hint", "description": "Progressive hint without revealing the answer"},
    {"id": "debug", "label": "Debug", "description": "Why my code fails, on the failing case"},
    {"id": "solution", "label": "Get Solution", "description": "Canonical solution with a walkthrough"},
    {"id": "explain_code", "label": "Explain Code", "description": "Line-by-line explanation of my code"},
    {"id": "complexity", "label": "Complexity", "description": "Time and space Big-O analysis"},
    {"id": "edge_cases", "label": "Edge Cases", "description": "Edge cases my code may miss"},
    {"id": "testcases", "label": "Generate Testcases", "description": "New sample inputs with expected outputs"},
    {"id": "optimize", "label": "Optimize", "description": "Faster / cleaner version of my code"},
]

SYSTEM_PROMPT = (
    "You are CodeForge AI, the built-in coding assistant of a LeetCode-style practice platform.\n"
    "Be concise, warm and educational. Use GitHub-flavored markdown.\n"
    "Rules:\n"
    "- Put code in fenced blocks with the language tag.\n"
    "- Prefer short paragraphs and bullet points.\n"
    "- Never invent platform details (tests, limits) that were not provided in the context.\n"
    "- For hint requests: give exactly ONE hint at the requested level and never the full solution "
    "unless the request type is 'solution'.\n"
    "- If the user's code is provided, ground every answer in that code.\n"
)


# ── error helper ───────────────────────────────────────────────────────────
def _error(status: int, kind: str, message: str, retryable: bool = False) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": kind, "message": message, "retryable": retryable},
    )


# ── context builders ───────────────────────────────────────────────────────
def _problem_context(problem: Optional[Problem], include_solution: bool = False) -> str:
    if not problem:
        return ""
    topics = json.loads(problem.topics) if problem.topics else []
    constraints = json.loads(problem.constraints) if problem.constraints else []
    examples = json.loads(problem.examples) if problem.examples else []
    hints = json.loads(problem.hints) if problem.hints else []

    parts = [
        f"Problem: {problem.title} (difficulty: {problem.difficulty})",
        f"Topics: {', '.join(topics) or 'n/a'}",
        "",
        "Description:",
        problem.description or "",
        "",
        "Examples:",
    ]
    for ex in examples:
        parts.append(
            f"- Input: {ex.get('input', '')} | Output: {ex.get('output', '')} | "
            f"Explanation: {ex.get('explanation', '')}"
        )
    parts.append("")
    parts.append("Constraints:")
    parts.extend(f"- {c}" for c in constraints)
    if hints:
        parts.append("")
        parts.append(f"Stored hints ({len(hints)}): " + " | ".join(hints[:3]))
    if problem.complexity_time or problem.complexity_space:
        parts.append(f"Expected complexity: time {problem.complexity_time}, space {problem.complexity_space}")
    if include_solution and problem.reference_solution:
        parts += [
            "",
            "Canonical reference solution (Python):",
            "```python",
            problem.reference_solution,
            "```",
        ]
        if problem.solution_explanation:
            parts += ["", "Stored solution explanation:", problem.solution_explanation]
    return "\n".join(parts)


def _run_result_context(run_result: Optional[dict]) -> str:
    if not run_result:
        return ""
    lines = [f"Latest judge result: {run_result.get('status', 'unknown')}"]
    if run_result.get("error_message"):
        lines.append(f"Error: {run_result['error_message']}")
    if run_result.get("stdout"):
        lines.append(f"Program output:\n{run_result['stdout'][:1500]}")
    for tr in (run_result.get("test_results") or [])[:3]:
        flag = "PASS" if tr.get("passed") else "FAIL"
        lines.append(
            f"[{flag}] input={tr.get('input_data', '')} "
            f"expected={tr.get('expected_output', '')} actual={tr.get('actual_output', '')}"
        )
    if run_result.get("total_passed") is not None:
        lines.append(
            f"Score: {run_result.get('total_passed')}/{run_result.get('total_passed', 0) + run_result.get('total_failed', 0)}"
        )
    return "\n".join(lines)


ACTION_PROMPTS = {
    "chat": "Answer the user's message about this problem or their code.",
    "explain_problem": "Explain the problem statement in plain English: what is being asked, "
    "what the input/output mean, and walk through the given examples step by step. "
    "Do not reveal a full solution.",
    "hint": "Give ONE progressive hint at the requested level. Level 1: nudge about the idea. "
    "Level 2: name the technique/pattern. Level 3: sketch the approach without full code. "
    "Do not give the complete solution unless level 3 AND the user explicitly asks.",
    "debug": "Debug the user's code against the latest judge result. Point out the exact line(s) "
    "or logic that fails, explain why, and show the minimal fix.",
    "solution": "Present the canonical solution (use the reference solution from context if given), "
    "then walk through it and state the complexity.",
    "explain_code": "Explain the user's code line by line: what each block does and why.",
    "complexity": "Analyze the time and space complexity of the user's code and justify the Big-O.",
    "edge_cases": "List the edge cases the user's code must handle, and say which of them it "
    "currently mishandles (if any).",
    "testcases": "Generate 3-5 new test cases (input + expected output) that stress the problem's "
    "boundaries. Present them as a markdown table.",
    "optimize": "Suggest optimizations for the user's code. Show an improved version and explain "
    "the complexity difference.",
}


def _build_user_prompt(body: CopilotRequest, problem: Optional[Problem]) -> str:
    include_solution = body.request_type == "solution"
    sections: List[str] = []

    problem_block = _problem_context(problem, include_solution=include_solution)
    if problem_block:
        sections.append(problem_block)

    if body.code:
        sections.append(f"User's current {body.language} code:\n```{body.language}\n{body.code}\n```")
    elif body.request_type not in ("chat", "explain_problem", "hint", "solution"):
        sections.append("User's code: (not provided yet)")

    if body.testcase:
        sections.append(f"Test case in question: {body.testcase}")

    run_block = _run_result_context(body.run_result)
    if run_block:
        sections.append(run_block)

    action_line = ACTION_PROMPTS.get(body.request_type, ACTION_PROMPTS["chat"])
    if body.request_type == "hint":
        action_line = f"{action_line} Requested hint level: {body.hint_level}."
    sections.append(f"Task: {action_line}")

    if body.request_type == "chat" and body.message:
        sections.append(f"User message: {body.message}")
    elif body.message:
        sections.append(f"User message: {body.message}")
    else:
        sections.append(f"User message: (none — perform the task above)")

    return "\n\n".join(sections)


# ── conversation helpers ───────────────────────────────────────────────────
def _load_conversation(
    db: Session, user: User, body: CopilotRequest
) -> Tuple[AIConversation, List[AIMessage]]:
    conversation = None
    if body.conversation_id:
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.id == body.conversation_id,
                AIConversation.user_id == user.id,
            )
            .first()
        )
    if conversation is None and body.problem_id:
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.user_id == user.id,
                AIConversation.problem_id == body.problem_id,
            )
            .order_by(AIConversation.created_at.desc())
            .first()
        )
    if conversation is None:
        conversation = AIConversation(
            user_id=user.id,
            problem_id=body.problem_id,
            title=(body.message or body.request_type)[:100],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history = (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation.id)
        .order_by(AIMessage.created_at.desc())
        .limit(12)
        .all()
    )
    history.reverse()
    return conversation, history


def _messages_payload(history: List[AIMessage], user_prompt: str) -> List[dict]:
    payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        if msg.role in ("user", "assistant") and msg.content:
            payload.append({"role": msg.role, "content": msg.content})
    payload.append({"role": "user", "content": user_prompt})
    return payload


def _save_turn(db: Session, conversation_id: int, user_prompt: str, reply: str, tokens: int):
    db.add(AIMessage(conversation_id=conversation_id, role="user", content=user_prompt[:8000]))
    db.add(
        AIMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=reply[:12000],
            tokens_used=tokens or None,
        )
    )
    db.commit()


def _next_hint_level(body: CopilotRequest) -> int:
    return min(body.hint_level + 1, 3) if body.request_type == "hint" else body.hint_level


# ── routes ─────────────────────────────────────────────────────────────────
@router.get("/ai/copilot/actions")
async def copilot_actions():
    return {"actions": QUICK_ACTIONS, "request_types": [a["id"] for a in QUICK_ACTIONS]}


@router.post("/ai/copilot", response_model=CopilotResponse)
async def copilot(
    body: CopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    from app.api.ai import _check_rate_limit

    if not _check_rate_limit(current_user.id, "copilot", settings.rate_limit_ai):
        return _error(429, "rate_limit", "Rate limit exceeded. Try again in a minute.", True)

    problem = None
    if body.problem_id:
        problem = (
            db.query(Problem)
            .filter(
                Problem.id == body.problem_id,
                Problem.status == ProblemStatus.PUBLISHED.value,
            )
            .first()
        )
        if not problem:
            return _error(404, "not_found", "Problem not found.")

    conversation, history = _load_conversation(db, current_user, body)
    user_prompt = _build_user_prompt(body, problem)
    messages = _messages_payload(history, user_prompt)

    try:
        reply, tokens = await get_mistral_service().chat(messages, max_tokens=2000, temperature=0.6)
    except MistralError as exc:
        return _error(exc.status_code, exc.kind, exc.message, exc.retryable)

    _save_turn(db, conversation.id, user_prompt, reply, tokens)
    return CopilotResponse(
        reply=reply,
        request_type=body.request_type,
        conversation_id=conversation.id,
        hint_level=_next_hint_level(body),
        tokens_used=tokens,
    )


@router.post("/ai/copilot/stream")
async def copilot_stream(
    body: CopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    from app.api.ai import _check_rate_limit

    if not _check_rate_limit(current_user.id, "copilot", settings.rate_limit_ai):
        return _error(429, "rate_limit", "Rate limit exceeded. Try again in a minute.", True)

    problem = None
    if body.problem_id:
        problem = (
            db.query(Problem)
            .filter(
                Problem.id == body.problem_id,
                Problem.status == ProblemStatus.PUBLISHED.value,
            )
            .first()
        )
        if not problem:
            return _error(404, "not_found", "Problem not found.")

    conversation, history = _load_conversation(db, current_user, body)
    user_prompt = _build_user_prompt(body, problem)
    messages = _messages_payload(history, user_prompt)
    conversation_id = conversation.id
    hint_level = _next_hint_level(body)

    async def event_stream():
        collected: List[str] = []
        try:
            async for delta in get_mistral_service().chat_stream(
                messages, max_tokens=2000, temperature=0.6
            ):
                collected.append(delta)
                yield f"data: {json.dumps({'type': 'delta', 'text': delta})}\n\n"
            reply = "".join(collected)
            if not reply.strip():
                raise MistralError(
                    "empty_response",
                    "AI service returned an empty response. Please try again.",
                    status_code=502,
                    retryable=True,
                )
            # fresh session: the request-scoped one is closed once streaming starts
            session = SessionLocal()
            try:
                _save_turn(session, conversation_id, user_prompt, reply, 0)
            finally:
                session.close()
            done_event = {
                "type": "done",
                "conversation_id": conversation_id,
                "request_type": body.request_type,
                "hint_level": hint_level,
            }
            yield f"data: {json.dumps(done_event)}\n\n"
        except MistralError as exc:
            error_event = {"type": "error", **exc.payload()}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception:  # noqa: BLE001
            fallback = {
                "type": "error",
                "error": "unknown",
                "message": "Unexpected AI error. Please try again.",
                "retryable": True,
            }
            yield f"data: {json.dumps(fallback)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
