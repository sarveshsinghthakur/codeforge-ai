"""Submissions API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_user
from app.core.exceptions import ProblemNotFound, SubmissionNotFound, Unauthorized, PaymentRequired
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission
from app.models.test_case import TestCase
from app.models.user import User
from app.models.user_progress import UserProblemProgress
from app.schemas.submission import (
    SubmissionCreateRequest as SubmissionCreate, SubmissionResult, TestResult, SubmissionListResponse, SubmissionDetailResponse,
)
from app.services.code_execution import get_execution_service
from app.services import access as premium_access
from app.utils.helpers import parse_json_field
import json
from datetime import datetime, timezone

router = APIRouter()


@router.get("/languages")
async def list_languages():
    """Runtimes the executor can actually run on this server."""
    return {"languages": get_execution_service().available_languages()}


@router.post("/submissions", response_model=SubmissionResult, status_code=201)
async def create_submission(
    body: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not current_user:
        raise Unauthorized("Authentication required")

    problem = db.query(Problem).filter(
        Problem.id == body.problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()

    # Medium/Hard problems require an active premium subscription
    if premium_access.is_locked(problem, premium_access.has_premium(db, current_user)):
        raise PaymentRequired(
            f"The '{problem.difficulty}' problem '{problem.title}' requires a premium subscription",
            details={"title": problem.title, "slug": problem.slug, "difficulty": problem.difficulty},
        )

    is_submit = body.mode == "submit"
    is_custom = body.mode == "custom"

    if is_custom and not (body.custom_input or "").strip():
        raise HTTPException(status_code=400, detail="custom_input is required when mode is 'custom'")

    submission = None
    if is_submit:
        submission = Submission(
            user_id=current_user.id,
            problem_id=body.problem_id,
            language=body.language,
            source_code=body.source_code,
            status="pending",
            total_count=0,
            passed_count=0,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        problem.attempt_count += 1

    if is_custom:
        # single user-provided input; expected output is unknown, so the
        # endpoint reports completion rather than pass/fail.
        active_case_dicts = [
            {"input": body.custom_input, "output": "", "is_public": True}
        ]
    else:
        test_cases = (
            db.query(TestCase)
            .filter(TestCase.problem_id == body.problem_id)
            .order_by(TestCase.order_index)
            .all()
        )

        if not test_cases:
            examples = parse_json_field(problem.examples, [])
            for i, ex in enumerate(examples):
                tc = TestCase(
                    problem_id=problem.id,
                    input_data=str(ex.get("input", f"test_{i}")),
                    expected_output=str(ex.get("output", "")),
                    is_public=(i < min(2, len(examples))),
                    order_index=i,
                )
                db.add(tc)
            db.commit()
            test_cases = db.query(TestCase).filter(TestCase.problem_id == problem.id).all()
            if submission:
                submission.total_count = len(test_cases)

        # run mode: public cases only; submit mode: everything (hidden never returned)
        active_cases = [tc for tc in test_cases if tc.is_public] if not is_submit else test_cases
        active_case_dicts = [
            {"input": tc.input_data, "output": tc.expected_output, "is_public": tc.is_public}
            for tc in active_cases
        ]

    executor = get_execution_service()
    result = await executor.execute(
        code=body.source_code,
        language=body.language,
        test_cases=active_case_dicts,
    )

    if is_custom and result.get("status") in ("accepted", "wrong_answer"):
        result = {**result, "status": "completed"}

    now_iso = datetime.now(timezone.utc).isoformat()
    if is_submit:
        submission.status = result["status"]
        submission.runtime_ms = result.get("runtime_ms")
        submission.memory_kb = result.get("memory_kb")
        submission.stdout = result.get("stdout")
        submission.stderr = result.get("stderr")
        submission.error_message = result.get("error_message")
        submission.passed_count = result.get("total_passed", 0)
        submission.total_count = len(active_case_dicts)
        db.commit()
        db.refresh(submission)
        now_iso = submission.created_at.isoformat()

        if result["status"] == "accepted":
            problem.solved_count += 1
            total_subs = db.query(Submission).filter(Submission.problem_id == problem.id).count()
            if total_subs > 0:
                problem.acceptance_rate = round(problem.solved_count / total_subs * 100, 1)

        # progress row: created on accepted always, or on any submit that flushes solve time
        flush_time = body.time_spent or 0
        if result["status"] == "accepted" or flush_time > 0:
            progress = db.query(UserProblemProgress).filter(
                UserProblemProgress.user_id == current_user.id,
                UserProblemProgress.problem_id == problem.id,
            ).first()

            today = datetime.now(timezone.utc).date().isoformat()

            if not progress:
                progress = UserProblemProgress(
                    user_id=current_user.id, problem_id=problem.id, solved=False,
                    attempt_count=0, solved_at=None,
                    last_attempt_at=datetime.now(timezone.utc), last_language=body.language,
                    current_streak_day=today, time_spent_seconds=0,
                )
                db.add(progress)

            if flush_time > 0:
                progress.time_spent_seconds = (progress.time_spent_seconds or 0) + flush_time

            if result["status"] == "accepted":
                if not progress.solved:
                    progress.solved = True
                    progress.solved_at = datetime.now(timezone.utc)
                progress.attempt_count += 1
                progress.last_attempt_at = datetime.now(timezone.utc)
                progress.last_language = body.language
                progress.current_streak_day = today

            db.commit()
        db.refresh(problem)

    # public-only view of the per-case results (hidden inputs/outputs never leak)
    test_results = []
    number = 0
    for tr in result.get("test_results", []):
        if not tr.get("is_public", True):
            continue
        number += 1
        test_results.append(
            TestResult(
                test_number=number,
                input_data=tr.get("input_data", ""),
                expected_output=tr.get("expected_output", ""),
                actual_output=tr.get("actual_output", ""),
                passed=bool(tr.get("passed", False)),
                is_public=True,
            )
        )

    return SubmissionResult(
        id=submission.id if submission else None,
        public_id=submission.public_id if submission else None,
        problem_id=submission.problem_id if submission else body.problem_id,
        language=body.language,
        mode=body.mode,
        status=result["status"],
        runtime_ms=result.get("runtime_ms"),
        memory_kb=result.get("memory_kb"),
        stdout=result.get("stdout"),
        stderr=result.get("stderr"),
        error_message=result.get("error_message"),
        passed_count=result.get("total_passed", 0),
        total_count=result.get("total_passed", 0) + result.get("total_failed", 0),
        created_at=now_iso,
        test_results=test_results,
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(submission_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise SubmissionNotFound()
    if submission.user_id != current_user.id and current_user.role != "ADMIN":
        raise Unauthorized()

    problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    test_cases = db.query(TestCase).filter(
        TestCase.problem_id == submission.problem_id,
        TestCase.is_public == True,
    ).order_by(TestCase.order_index).all()

    test_results = []
    for i, tc in enumerate(test_cases):
        test_results.append(TestResult(
            test_number=i + 1, input_data=tc.input_data,
            expected_output=tc.expected_output, actual_output="",
            passed=submission.status == "accepted", is_public=True,
        ))

    return SubmissionDetailResponse(
        id=submission.id, public_id=submission.public_id,
        problem_id=submission.problem_id,
        problem_title=problem.title if problem else "",
        problem_slug=problem.slug if problem else "",
        language=submission.language, status=submission.status,
        runtime_ms=submission.runtime_ms, memory_kb=submission.memory_kb,
        source_code=submission.source_code, stdout=submission.stdout,
        stderr=submission.stderr, error_message=submission.error_message,
        passed_count=submission.passed_count, total_count=submission.total_count,
        created_at=submission.created_at.isoformat(),
        test_results=test_results,
    )


@router.get("/problems/{problem_id}/submissions", response_model=List[SubmissionListResponse])
async def get_problem_submissions(
    problem_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not current_user:
        raise Unauthorized("Authentication required")
    submissions = db.query(Submission).filter(
        Submission.problem_id == problem_id,
        Submission.user_id == current_user.id,
    ).order_by(desc(Submission.created_at)).offset(offset).limit(limit).all()

    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    p_title = problem.title if problem else ""
    p_slug = problem.slug if problem else ""

    return [
        SubmissionListResponse(
            id=s.id, public_id=s.public_id, problem_id=s.problem_id,
            problem_title=p_title, problem_slug=p_slug,
            language=s.language, status=s.status,
            runtime_ms=s.runtime_ms, memory_kb=s.memory_kb,
            created_at=s.created_at.isoformat(),
        )
        for s in submissions
    ]


@router.get("/problems/slug/{slug}/submissions", response_model=List[SubmissionListResponse])
async def get_problem_submissions_by_slug(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not current_user:
        raise Unauthorized("Authentication required")
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise ProblemNotFound()
    submissions = db.query(Submission).filter(
        Submission.problem_id == problem.id,
        Submission.user_id == current_user.id,
    ).order_by(desc(Submission.created_at)).offset(offset).limit(limit).all()

    return [
        SubmissionListResponse(
            id=s.id, public_id=s.public_id, problem_id=s.problem_id,
            problem_title=problem.title, problem_slug=problem.slug,
            language=s.language, status=s.status,
            runtime_ms=s.runtime_ms, memory_kb=s.memory_kb,
            created_at=s.created_at.isoformat(),
        )
        for s in submissions
    ]


@router.get("/users/me/submissions", response_model=List[SubmissionListResponse])
async def get_my_submissions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    submissions = db.query(Submission).filter(
        Submission.user_id == current_user.id,
    ).order_by(desc(Submission.created_at)).offset(offset).limit(limit).all()

    result = []
    for s in submissions:
        problem = db.query(Problem).filter(Problem.id == s.problem_id).first()
        result.append(SubmissionListResponse(
            id=s.id, public_id=s.public_id, problem_id=s.problem_id,
            problem_title=problem.title if problem else "Unknown",
            problem_slug=problem.slug if problem else "",
            language=s.language, status=s.status,
            runtime_ms=s.runtime_ms, memory_kb=s.memory_kb,
            created_at=s.created_at.isoformat(),
        ))
    return result
