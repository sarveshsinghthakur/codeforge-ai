"""Problems API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_user, require_admin
from app.core.exceptions import ProblemNotFound, NotFound, Conflict, PaymentRequired
from app.models.problem import Problem, ProblemStatus
from app.models.test_case import TestCase
from app.models.user import User
from app.models.user_progress import UserProblemProgress
from app.models.favorite import UserFavorite
from app.schemas.problem import (
    ProblemCreateRequest as ProblemCreate, ProblemUpdateRequest as ProblemUpdate,
    ProblemListResponse, ProblemListEnvelope, ProblemDetailResponse,
    ProblemSearchParams as ProblemListParams, ProblemGenerateRequest, ProblemGenerateResponse,
)
from app.schemas.submission import SubmissionResult, TestResult as TR
from app.services.code_execution import CodeExecutionService, get_execution_service
from app.services import access as premium_access
from app.services.mistral_service import MistralService, get_mistral_service
from app.services.quality_checker import ProblemQualityChecker, get_quality_checker
from app.core.config import settings
from app.utils.helpers import slugify, format_json_field, parse_json_field
import json
import hashlib
from datetime import datetime, timezone

router = APIRouter()


def _user_flags(db: Session, user: Optional[User], problem_ids: List[int]):
    """Return (solved_ids, favorite_ids) for the given problems and user."""
    if not user or not problem_ids:
        return set(), set()
    solved = {
        row[0]
        for row in db.query(UserProblemProgress.problem_id)
        .filter(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id.in_(problem_ids),
            UserProblemProgress.solved == True,  # noqa: E712
        )
        .all()
    }
    favorites = {
        row[0]
        for row in db.query(UserFavorite.problem_id)
        .filter(
            UserFavorite.user_id == user.id,
            UserFavorite.problem_id.in_(problem_ids),
        )
        .all()
    }
    return solved, favorites


@router.get("/problems", response_model=ProblemListEnvelope)
async def list_problems(
    params: ProblemListParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    query = db.query(Problem).filter(Problem.status == ProblemStatus.PUBLISHED.value)

    if params.q:
        search = f"%{params.q}%"
        query = query.filter(
            or_(
                Problem.title.ilike(search),
                Problem.slug.ilike(search),
                Problem.description.ilike(search),
            )
        )

    if params.difficulty:
        query = query.filter(Problem.difficulty == params.difficulty)

    if params.topic:
        # topics is a JSON-encoded text column -> match the quoted topic token
        query = query.filter(Problem.topics.like(f'%"{params.topic}"%'))

    if params.company:
        query = query.filter(Problem.company.ilike(f"%{params.company}%"))

    if params.status and current_user:
        solved_sub = (
            db.query(UserProblemProgress.problem_id)
            .filter(
                UserProblemProgress.user_id == current_user.id,
                UserProblemProgress.solved == True,  # noqa: E712
            )
            .subquery()
        )
        if params.status == "solved":
            query = query.filter(Problem.id.in_(solved_sub))
        elif params.status == "unsolved":
            query = query.filter(~Problem.id.in_(solved_sub))

    sort_column = {
        "difficulty": Problem.difficulty,
        "acceptance": Problem.acceptance_rate,
        "solved": Problem.solved_count,
        "recent": Problem.created_at,
    }.get(params.sort, Problem.created_at)

    if params.order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total = query.count()
    offset = (params.page - 1) * params.limit
    problems = query.offset(offset).limit(params.limit).all()

    solved_ids, favorite_ids = _user_flags(db, current_user, [p.id for p in problems])
    premium = premium_access.has_premium(db, current_user)

    return ProblemListEnvelope(
        items=[
            ProblemListResponse(
                id=p.id,
                public_id=p.public_id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                acceptance_rate=round(p.acceptance_rate, 1),
                solved_count=p.solved_count,
                attempt_count=p.attempt_count,
                topics=parse_json_field(p.topics, []),
                company=p.company,
                created_at=p.created_at.isoformat(),
                is_solved=p.id in solved_ids,
                is_favorite=p.id in favorite_ids,
                is_locked=premium_access.is_locked(p, premium),
            )
            for p in problems
        ],
        total=total,
        page=params.page,
        limit=params.limit,
    )


def _list_item(db: Session, user: Optional[User], p: Problem) -> ProblemListResponse:
    solved_ids, favorite_ids = _user_flags(db, user, [p.id])
    premium = premium_access.has_premium(db, user)
    return ProblemListResponse(
        id=p.id,
        public_id=p.public_id,
        title=p.title,
        slug=p.slug,
        difficulty=p.difficulty,
        acceptance_rate=round(p.acceptance_rate, 1),
        solved_count=p.solved_count,
        attempt_count=p.attempt_count,
        topics=parse_json_field(p.topics, []),
        company=p.company,
        created_at=p.created_at.isoformat(),
        is_solved=p.id in solved_ids,
        is_favorite=p.id in favorite_ids,
        is_locked=premium_access.is_locked(p, premium),
    )


@router.get("/problems/daily", response_model=ProblemListResponse)
async def daily_problem(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Same problem for every user all day — deterministic pick from date."""
    rows = (
        db.query(Problem.id)
        .filter(Problem.status == ProblemStatus.PUBLISHED.value)
        .order_by(Problem.id.asc())
        .all()
    )
    if not rows:
        raise ProblemNotFound()
    day = datetime.now(timezone.utc).date().isoformat()
    idx = int(hashlib.sha256(day.encode()).hexdigest(), 16) % len(rows)
    problem = db.query(Problem).filter(Problem.id == rows[idx][0]).first()
    if problem is None:
        raise ProblemNotFound()
    return _list_item(db, current_user, problem)


@router.get("/problems/random", response_model=ProblemListResponse)
async def random_problem(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    problem = (
        db.query(Problem)
        .filter(Problem.status == ProblemStatus.PUBLISHED.value)
        .order_by(func.random())
        .first()
    )
    if problem is None:
        raise ProblemNotFound()
    return _list_item(db, current_user, problem)


@router.get("/problems/search", response_model=List[ProblemListResponse])
async def search_problems(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    search = f"%{q}%"
    problems = (
        db.query(Problem)
        .filter(
            Problem.status == ProblemStatus.PUBLISHED.value,
            or_(
                Problem.title.ilike(search),
                Problem.slug.ilike(search),
                Problem.description.ilike(search),
            ),
        )
        .order_by(Problem.solved_count.desc())
        .limit(limit)
        .all()
    )
    solved_ids, favorite_ids = _user_flags(db, current_user, [p.id for p in problems])
    premium = premium_access.has_premium(db, current_user)
    return [
        ProblemListResponse(
            id=p.id, public_id=p.public_id, title=p.title, slug=p.slug,
            difficulty=p.difficulty, acceptance_rate=round(p.acceptance_rate, 1),
            solved_count=p.solved_count, attempt_count=p.attempt_count,
            topics=parse_json_field(p.topics, []), company=p.company,
            created_at=p.created_at.isoformat(),
            is_solved=p.id in solved_ids,
            is_favorite=p.id in favorite_ids,
            is_locked=premium_access.is_locked(p, premium),
        )
        for p in problems
    ]


@router.get("/problems/stats")
async def problems_stats(db: Session = Depends(get_db)):
    """Lightweight counts for the landing/dashboard stat cards."""
    rows = (
        db.query(Problem.difficulty, func.count(Problem.id))
        .filter(Problem.status == ProblemStatus.PUBLISHED.value)
        .group_by(Problem.difficulty)
        .all()
    )
    counts = {row[0]: row[1] for row in rows}
    return {
        "total": sum(counts.values()),
        "easy": counts.get("easy", 0),
        "medium": counts.get("medium", 0),
        "hard": counts.get("hard", 0),
    }


@router.get("/problems/favorites", response_model=List[ProblemListResponse])
@router.get("/users/me/favorites", response_model=List[ProblemListResponse])
async def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    rows = (
        db.query(Problem, UserFavorite)
        .join(UserFavorite, UserFavorite.problem_id == Problem.id)
        .filter(UserFavorite.user_id == current_user.id)
        .order_by(UserFavorite.created_at.desc())
        .all()
    )
    premium = premium_access.has_premium(db, current_user)
    return [
        ProblemListResponse(
            id=p.id, public_id=p.public_id, title=p.title, slug=p.slug,
            difficulty=p.difficulty, acceptance_rate=round(p.acceptance_rate, 1),
            solved_count=p.solved_count, attempt_count=p.attempt_count,
            topics=parse_json_field(p.topics, []), company=p.company,
            created_at=p.created_at.isoformat(),
            is_solved=False, is_favorite=True,
            is_locked=premium_access.is_locked(p, premium),
        )
        for p, _ in rows
    ]


@router.post("/problems/{problem_id}/favorite")
async def add_favorite(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    problem = db.query(Problem).filter(
        Problem.id == problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.problem_id == problem_id,
    ).first()
    if not existing:
        db.add(UserFavorite(user_id=current_user.id, problem_id=problem_id))
        db.commit()
    return {"favorite": True, "problem_id": problem_id}


@router.delete("/problems/{problem_id}/favorite")
async def remove_favorite(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.problem_id == problem_id,
    ).delete()
    db.commit()
    return {"favorite": False, "problem_id": problem_id}


@router.get("/problems/{problem_id}", response_model=ProblemDetailResponse)
async def get_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    problem = db.query(Problem).filter(
        Problem.id == problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()
    return _problem_to_detail(problem, db, current_user)


@router.get("/problems/slug/{slug}", response_model=ProblemDetailResponse)
async def get_problem_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    problem = db.query(Problem).filter(
        Problem.slug == slug,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()
    return _problem_to_detail(problem, db, current_user)


def _problem_to_detail(
    problem: Problem, db: Session, current_user: Optional[User] = None
) -> ProblemDetailResponse:
    # Medium/Hard problems require an active premium subscription
    premium = premium_access.has_premium(db, current_user)
    if premium_access.is_locked(problem, premium):
        raise PaymentRequired(
            f"The '{problem.difficulty}' problem '{problem.title}' requires a premium subscription",
            details={
                "title": problem.title,
                "slug": problem.slug,
                "difficulty": problem.difficulty,
            },
        )

    # only public cases are ever exposed to the workspace UI
    test_cases = (
        db.query(TestCase)
        .filter(TestCase.problem_id == problem.id, TestCase.is_public == True)  # noqa: E712
        .order_by(TestCase.order_index)
        .all()
    )
    hidden_count = (
        db.query(TestCase)
        .filter(TestCase.problem_id == problem.id, TestCase.is_public == False)  # noqa: E712
        .count()
    )
    solved_ids, favorite_ids = _user_flags(db, current_user, [problem.id])

    return ProblemDetailResponse(
        id=problem.id,
        public_id=problem.public_id,
        title=problem.title,
        slug=problem.slug,
        difficulty=problem.difficulty,
        acceptance_rate=round(problem.acceptance_rate, 1),
        solved_count=problem.solved_count,
        attempt_count=problem.attempt_count,
        description=problem.description,
        topics=parse_json_field(problem.topics, []),
        constraints=parse_json_field(problem.constraints, []),
        examples=parse_json_field(problem.examples, []),
        hints=parse_json_field(problem.hints, []),
        follow_up=problem.follow_up,
        starter_code=parse_json_field(problem.starter_code, {}),
        solution_explanation=problem.solution_explanation,
        complexity_time=problem.complexity_time,
        complexity_space=problem.complexity_space,
        company=problem.company,
        related_problems=parse_json_field(problem.related_problems, []),
        test_cases=[
            {
                "id": tc.id,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_public": tc.is_public,
                "is_edge_case": tc.is_edge_case,
                "edge_case_category": tc.edge_case_category,
                "order_index": tc.order_index,
            }
            for tc in test_cases
        ],
        hidden_test_case_count=hidden_count,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        created_at=problem.created_at.isoformat(),
        updated_at=problem.updated_at.isoformat(),
        is_solved=problem.id in solved_ids,
        is_favorite=problem.id in favorite_ids,
    )


@router.get("/problems/{problem_id}/progress")
async def get_problem_progress(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    progress = db.query(UserProblemProgress).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.problem_id == problem_id,
    ).first()
    if not progress:
        return {"solved": False, "attempt_count": 0, "last_attempt_at": None}
    return {
        "solved": progress.solved,
        "attempt_count": progress.attempt_count,
        "last_attempt_at": progress.last_attempt_at.isoformat() if progress.last_attempt_at else None,
    }


@router.post("/problems/{problem_id}/progress")
async def update_problem_progress(
    problem_id: int,
    solved: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ProblemNotFound()

    progress = db.query(UserProblemProgress).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.problem_id == problem_id,
    ).first()

    today = datetime.now(timezone.utc).date().isoformat()

    if not progress:
        progress = UserProblemProgress(
            user_id=current_user.id, problem_id=problem_id, solved=solved,
            attempt_count=1, solved_at=datetime.now(timezone.utc) if solved else None,
            last_attempt_at=datetime.now(timezone.utc), last_language="python",
            current_streak_day=today,
        )
        db.add(progress)
    else:
        progress.attempt_count += 1
        progress.last_attempt_at = datetime.now(timezone.utc)
        if solved and not progress.solved:
            progress.solved = True
            progress.solved_at = datetime.now(timezone.utc)
            problem.solved_count += 1
        progress.current_streak_day = today

    db.commit()
    db.refresh(problem)
    return {"solved": progress.solved, "attempt_count": progress.attempt_count}


# ─── Admin Problem Management ────────────────────────────────────────────────

@router.post("/admin/problems", response_model=ProblemDetailResponse, status_code=201)
async def create_problem(
    body: ProblemCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if db.query(Problem).filter(Problem.slug == body.slug).first():
        raise Conflict("Slug already exists")

    problem = Problem(
        title=body.title,
        slug=body.slug,
        difficulty=body.difficulty,
        description=body.description,
        topics=format_json_field(body.topics),
        constraints=format_json_field(body.constraints),
        examples=format_json_field(body.examples),
        hints=format_json_field(body.hints),
        follow_up=body.follow_up,
        starter_code=format_json_field(body.starter_code),
        reference_solution=body.reference_solution,
        solution_explanation=body.solution_explanation,
        complexity_time=body.complexity_time,
        complexity_space=body.complexity_space,
        company=body.company,
        related_problems=format_json_field(body.related_problems),
        status=body.status or ProblemStatus.DRAFT.value,
        time_limit_ms=body.time_limit_ms or 2000,
        memory_limit_mb=body.memory_limit_mb or 256,
        created_by=admin.id,
    )
    db.add(problem)
    db.flush()

    if body.test_cases:
        for i, tc in enumerate(body.test_cases):
            test_case = TestCase(
                problem_id=problem.id,
                input_data=tc.input_data,
                expected_output=tc.expected_output,
                is_public=tc.is_public,
                is_edge_case=tc.is_edge_case,
                edge_case_category=tc.edge_case_category,
                order_index=i,
            )
            db.add(test_case)

    db.commit()
    db.refresh(problem)
    return _problem_to_detail(problem, db)


@router.put("/admin/problems/{problem_id}", response_model=ProblemDetailResponse)
async def update_problem(
    problem_id: int,
    body: ProblemUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ProblemNotFound()

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "test_cases":
            # Replace all test cases
            db.query(TestCase).filter(TestCase.problem_id == problem_id).delete()
            if value:
                for i, tc in enumerate(value):
                    test_case = TestCase(
                        problem_id=problem_id,
                        input_data=tc.input_data,
                        expected_output=tc.expected_output,
                        is_public=tc.is_public,
                        is_edge_case=tc.is_edge_case,
                        edge_case_category=tc.edge_case_category,
                        order_index=i,
                    )
                    db.add(test_case)
        elif field in ["topics", "constraints", "examples", "hints", "starter_code", "related_problems"]:
            setattr(problem, field, format_json_field(value))
        else:
            setattr(problem, field, value)

    db.commit()
    db.refresh(problem)
    return _problem_to_detail(problem, db)


@router.delete("/admin/problems/{problem_id}")
async def delete_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ProblemNotFound()
    db.delete(problem)
    db.commit()
    return {"message": "Problem deleted"}
