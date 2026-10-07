"""AI API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import require_user, require_admin
from app.core.config import settings
from app.core.exceptions import ProblemNotFound, NotFound
from app.core.prompts import TERSE_STYLE
from app.models.problem import Problem, ProblemStatus
from app.models.user import User
from app.models.ai import AIConversation, AIMessage, ProblemGeneration, ProblemGenerationTestCase
from app.schemas.ai import (
    AIChatRequest, AIChatResponse, AIAnalyzeRequest, AIAnalyzeResponse,
    HintRequest, HintResponse, TestGenerationRequest, TestGenerationResponse,
    GeneratedTestCase, TestVerifyRequest, TestVerifyResponse,
)
from app.services.mistral_service import MistralError, MistralService, get_mistral_service
from app.services.code_execution import CodeExecutionService, get_execution_service
from app.services.quality_checker import ProblemQualityChecker, get_quality_checker
import json
import structlog

logger = structlog.get_logger("codeforge")

router = APIRouter()

_rate_limit_cache: dict = {}


def _ai_error(exc: MistralError) -> JSONResponse:
    """Structured, secret-free AI failure body."""
    return JSONResponse(status_code=exc.status_code, content=exc.payload())

_rate_limit_cache: dict = {}


def _check_rate_limit(user_id: int, action: str, limit: int) -> bool:
    import time
    key = f"{user_id}:{action}"
    now = time.time()
    if key not in _rate_limit_cache:
        _rate_limit_cache[key] = []
    _rate_limit_cache[key] = [t for t in _rate_limit_cache[key] if now - t < 60]
    if len(_rate_limit_cache[key]) >= limit:
        return False
    _rate_limit_cache[key].append(now)
    return True


@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(
    body: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not _check_rate_limit(current_user.id, "ai_chat", settings.rate_limit_ai):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    mistral = get_mistral_service()

    problem_context = ""
    if body.problem_id:
        problem = db.query(Problem).filter(
            Problem.id == body.problem_id,
            Problem.status == ProblemStatus.PUBLISHED.value,
        ).first()
        if not problem:
            raise ProblemNotFound()

        constraints_list = json.loads(problem.constraints) if problem.constraints else []
        constraints_str = "\n".join(f"- {c}" for c in constraints_list)
        problem_context = (
            f"Problem: {problem.title}\n"
            f"Difficulty: {problem.difficulty}\n"
            f"Topics: {', '.join(json.loads(problem.topics) if problem.topics else [])}\n"
            f"Constraints:\n{constraints_str}\n"
            f"Description:\n{problem.description}\n"
            f"Examples:\n"
        )
        for ex in json.loads(problem.examples) if problem.examples else []:
            problem_context += (
                f"Input: {ex.get('input', '')}\n"
                f"Output: {ex.get('output', '')}\n"
                f"Explanation: {ex.get('explanation', '')}\n\n"
            )

    conversation = None
    if body.conversation_id:
        conversation = db.query(AIConversation).filter(
            AIConversation.id == body.conversation_id,
            AIConversation.user_id == current_user.id,
        ).first()

    if not conversation:
        conversation = AIConversation(
            user_id=current_user.id,
            problem_id=body.problem_id,
            title=body.message[:100],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    user_msg = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    db.commit()

    system_prompt = (
        "You are CodeForge AI, a helpful coding assistant for a competitive programming platform.\n\n"
        "Be encouraging, clear, and educational.\n\n"
        + TERSE_STYLE + "\n\n"
        + problem_context
    )

    messages = db.query(AIMessage).filter(
        AIMessage.conversation_id == conversation.id,
    ).order_by(AIMessage.created_at).limit(20).all()

    messages_payload = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        messages_payload.append({"role": msg.role, "content": msg.content})
    messages_payload.append({"role": "user", "content": body.message})

    try:
        response_text, tokens_used = await get_mistral_service().chat(
            messages_payload, max_tokens=2000, temperature=0.7
        )
    except MistralError as exc:
        logger.error("Mistral API error", kind=exc.kind)
        return _ai_error(exc)

    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        tokens_used=tokens_used,
    )
    db.add(assistant_msg)
    db.commit()

    return AIChatResponse(
        response=response_text,
        conversation_id=conversation.id,
        tokens_used=tokens_used,
    )


@router.post("/ai/analyze", response_model=AIAnalyzeResponse)
async def ai_analyze(
    body: AIAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not _check_rate_limit(current_user.id, "ai_analyze", settings.rate_limit_ai):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    mistral = get_mistral_service()

    problem_context = ""
    if body.problem_id:
        problem = db.query(Problem).filter(Problem.id == body.problem_id).first()
        if problem:
            problem_context = f"Problem: {problem.title}\n{problem.description}\n"

    analysis_type = body.analysis_type or "analyze"

    prompts = {
        "analyze": f"Analyze this {body.language} code for correctness, style issues, and potential bugs:\n\n{body.code}\n\nProvide a thorough analysis.",
        "bugs": f"Find all bugs and potential issues in this {body.language} code:\n\n{body.code}\n\nList each bug with explanation.",
        "complexity": f"Analyze the time and space complexity of this {body.language} code:\n\n{body.code}\n\nProvide Big-O analysis.",
        "optimize": f"Suggest optimizations for this {body.language} code:\n\n{body.code}\n\nProvide specific suggestions with code examples.",
        "explain": f"Explain what this {body.language} code does step by step:\n\n{body.code}\n\nProvide a detailed explanation.",
        "edge_cases": f"Identify edge cases that this {body.language} code might fail on:\n\n{body.code}\n\nList edge cases that could cause failures.",
        "explain_error": f"Explain why this code might be failing. Here's the code:\n\n{body.code}\n\nProvide possible reasons for errors.",
    }

    prompt = prompts.get(analysis_type, prompts["analyze"])
    if problem_context:
        prompt = problem_context + "\n\n" + prompt

    try:
        result = await mistral.analyze_code(
            code=body.code,
            language=body.language,
            problem_description=problem_context,
        )

        if not result:
            text = await mistral.generate_text(prompt)
            result = {
                "analysis": text,
                "suggestions": [],
                "complexity": {"time": "", "space": ""},
                "bugs": [],
                "edge_cases": [],
            }
    except MistralError as exc:
        logger.error("AI analyze error", kind=exc.kind)
        return _ai_error(exc)

    return AIAnalyzeResponse(
        analysis=result.get("analysis", ""),
        suggestions=result.get("suggestions", []),
        complexity=result.get("complexity"),
        potential_bugs=result.get("bugs", result.get("potential_bugs", [])),
        edge_cases=result.get("edge_cases", []),
    )


@router.post("/ai/hints", response_model=HintResponse)
async def ai_hints(
    body: HintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not _check_rate_limit(current_user.id, "ai_hints", settings.rate_limit_ai):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    problem = db.query(Problem).filter(
        Problem.id == body.problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()

    mistral = get_mistral_service()
    hints_data = json.loads(problem.hints) if problem.hints else []

    if body.hint_level <= len(hints_data):
        hint_text = hints_data[body.hint_level - 1]
    else:
        topics = json.loads(problem.topics) if problem.topics else []
        constraints = json.loads(problem.constraints) if problem.constraints else []
        examples = json.loads(problem.examples) if problem.examples else []

        prompt = (
            f"Generate hint level {body.hint_level} for this problem.\n\n"
            f"Problem: {problem.title}\n"
            f"Difficulty: {problem.difficulty}\n"
            f"Topics: {', '.join(topics)}\n"
            f"Constraints:\n" + "\n".join(f"- {c}" for c in constraints) +
            f"\nDescription:\n{problem.description}\n"
            f"Examples:\n" +
            "".join(f"Input: {e.get('input','')}\nOutput: {e.get('output','')}\n" for e in examples) +
            (f"\nUser code:\n{body.code}" if body.code else "") +
            f"\n\nHint levels:\n"
            f"- Level 1: Very subtle hint, don't reveal the solution\n"
            f"- Level 2: More specific hint about approach\n"
            f"- Level 3: Detailed hint, almost revealing the solution\n\n"
            f"Generate a helpful hint for level {body.hint_level}."
        )

        try:
            hint_text = await mistral.generate_text(prompt, max_tokens=500)
        except MistralError as exc:
            logger.error("AI hint generation error", kind=exc.kind)
            return _ai_error(exc)

    solution_revealed = body.hint_level >= 3

    return HintResponse(
        problem_id=problem.id,
        hint_level=body.hint_level,
        hint=hint_text,
        solution_revealed=solution_revealed,
    )


# ── Admin: Test case generation ─────────────────────────────────────────────

@router.post("/admin/ai/generate-test-cases", response_model=TestGenerationResponse)
async def generate_test_cases(
    body: TestGenerationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not _check_rate_limit(admin.id, "ai_generate_tc", settings.rate_limit_generate):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    problem = db.query(Problem).filter(Problem.id == body.problem_id).first()
    if not problem:
        raise ProblemNotFound()

    mistral = get_mistral_service()

    constraints_list = json.loads(problem.constraints) if problem.constraints else []
    constraints_str = "\n".join(f"- {c}" for c in constraints_list)
    examples_list = json.loads(problem.examples) if problem.examples else []
    examples_str = "".join(f"Input: {e.get('input','')}\nOutput: {e.get('output','')}\n" for e in examples_list)

    prompt = (
        f"Generate {body.count} test cases for this problem.\n\n"
        f"Problem: {problem.title}\n"
        f"Difficulty: {problem.difficulty}\n"
        f"Description:\n{problem.description}\n"
        f"Constraints:\n{constraints_str}\n"
        f"Examples:\n{examples_str}\n"
        f"Reference solution:\n{body.reference_solution}\n\n"
        f"Generate diverse test cases covering:\n"
        f"- Basic cases\n"
        f"- Edge cases (empty input, single element, boundaries, etc.)\n"
        f"- Maximum constraints\n"
        f"- Minimum constraints\n\n"
        f"For each test case, provide:\n"
        f"- \"input\": The input data\n"
        f"- \"output\": The expected output\n"
        f"- \"category\": One of: basic, edge_case, boundary, max_constraint, min_constraint\n\n"
        f"Return ONLY a JSON array of test case objects."
    )

    try:
        cases = await mistral.generate_test_cases(
            problem={
                "title": problem.title,
                "description": problem.description,
                "constraints": json.loads(problem.constraints) if problem.constraints else [],
                "examples": json.loads(problem.examples) if problem.examples else [],
                "difficulty": problem.difficulty,
            },
            count=body.count,
        )

        if not cases or not isinstance(cases, list):
            raise ValueError("Invalid test case format from AI")

        generated = []
        for i, tc in enumerate(cases):
            input_data = str(tc.get("input", ""))
            expected_output = str(tc.get("output", ""))
            category = tc.get("category", "basic")

            verified = True
            actual_output = ""
            if problem.reference_solution:
                executor = get_execution_service()
                verify_result = await executor.execute(
                    code=problem.reference_solution,
                    language="python",
                    test_cases=[{"input": input_data, "output": expected_output}],
                )
                verified = verify_result["status"] == "accepted"
                if verify_result.get("test_results"):
                    actual_output = verify_result["test_results"][0].get("actual_output", "")

            generated.append(GeneratedTestCase(
                input_data=input_data,
                expected_output=expected_output,
                category=category,
                is_edge_case=category in ("edge_case", "boundary"),
            ))

        return TestGenerationResponse(
            generated_cases=generated,
            verified_count=sum(1 for g in generated if g.input_data != ""),
            failed_verification=sum(1 for g in generated if not verified),
            duplicate_count=0,
            warnings=[],
        )
    except MistralError as exc:
        logger.error("Test case generation error", kind=exc.kind)
        return _ai_error(exc)
    except Exception as e:
        logger.error("Test case generation error", error=str(e))
        return JSONResponse(
            status_code=502,
            content={
                "error": "generation_failed",
                "message": "Could not generate test cases from the AI response.",
                "retryable": True,
            },
        )


@router.post("/admin/ai/verify-test-case", response_model=TestVerifyResponse)
async def verify_test_case_endpoint(
    body: TestVerifyRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    executor = get_execution_service()
    result = await executor.execute(
        code=body.reference_solution,
        language=body.language,
        test_cases=[{"input": body.input_data, "output": body.expected_output}],
    )

    actual_output = ""
    if result.get("test_results"):
        actual_output = result["test_results"][0].get("actual_output", "")

    return TestVerifyResponse(
        verified=result["status"] == "accepted",
        actual_output=actual_output,
        match=result["status"] == "accepted",
        error=result.get("error_message"),
    )


@router.get("/admin/ai/quality-report", response_model=dict)
async def quality_report(
    generation_id: int = Query(..., description="Problem generation ID"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    generation = db.query(ProblemGeneration).filter(
        ProblemGeneration.id == generation_id,
    ).first()
    if not generation:
        raise NotFound("Generation")

    try:
        data = json.loads(generation.generated_data)
    except json.JSONDecodeError:
        return {"error": "Invalid generated data JSON"}

    test_cases = db.query(ProblemGenerationTestCase).filter(
        ProblemGenerationTestCase.generation_id == generation_id,
    ).all()

    tc_list = [
        {"input": tc.input_data, "output": tc.expected_output}
        for tc in test_cases
    ]

    checker = get_quality_checker()
    report = checker.check(
        data=data,
        reference_solution=data.get("reference_solution", ""),
        test_cases=tc_list,
    )

    return report
