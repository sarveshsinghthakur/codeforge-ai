"""Admin API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.security import require_admin
from app.core.exceptions import NotFound
from app.models.user import User
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission
from app.models.user_progress import UserProblemProgress
from app.models.ai import AIConversation, AIMessage, ProblemGeneration, ProblemGenerationTestCase, AuditLog
from app.schemas.discussion import (
    AdminUserResponse, AdminSubmissionResponse, AuditLogResponse,
)
from app.schemas.problem import ProblemListResponse, ProblemGenerateRequest, ProblemGenerateResponse
from app.services.mistral_service import MistralService, get_mistral_service
from app.services.code_execution import CodeExecutionService, get_execution_service
from app.services.quality_checker import ProblemQualityChecker, get_quality_checker
import json

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    total_users = db.query(User).count()
    active_7d = db.query(User).filter(User.created_at >= seven_days_ago).count()
    active_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    total_problems = db.query(Problem).count()
    published_problems = db.query(Problem).filter(Problem.status == ProblemStatus.PUBLISHED.value).count()
    total_submissions = db.query(Submission).count()
    accepted_submissions = db.query(Submission).filter(Submission.status == "accepted").count()
    acceptance_rate = round(accepted_submissions / total_submissions * 100, 1) if total_submissions > 0 else 0.0
    total_ai_requests = db.query(AIMessage).count()
    return {
        "total_users": total_users, "active_users_7d": active_7d, "active_users_30d": active_30d,
        "total_problems": total_problems, "published_problems": published_problems,
        "total_submissions": total_submissions, "accepted_submissions": accepted_submissions,
        "acceptance_rate": acceptance_rate, "total_ai_requests": total_ai_requests,
    }


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    offset = (page - 1) * limit
    users = db.query(User).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    result = []
    for u in users:
        solved = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == u.id, UserProblemProgress.solved == True,
        ).count()
        sub_count = db.query(Submission).filter(Submission.user_id == u.id).count()
        result.append(AdminUserResponse(
            id=u.id, public_id=u.public_id, username=u.username, email=u.email,
            role=u.role, is_active=u.is_active, problems_solved=solved,
            submission_count=sub_count, joined_at=u.created_at.isoformat(),
        ))
    return result


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFound("User")
    solved = db.query(UserProblemProgress).filter(
        UserProblemProgress.user_id == user.id, UserProblemProgress.solved == True,
    ).count()
    sub_count = db.query(Submission).filter(Submission.user_id == user.id).count()
    return AdminUserResponse(
        id=user.id, public_id=user.public_id, username=user.username, email=user.email,
        role=user.role, is_active=user.is_active, problems_solved=solved,
        submission_count=sub_count, joined_at=user.created_at.isoformat(),
    )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str = Query(..., pattern="^(USER|ADMIN)$"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFound("User")
    user.role = role
    db.commit()
    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFound("User")
    user.is_active = is_active
    db.commit()
    return {"message": f"User {'activated' if is_active else 'deactivated'}"}


@router.get("/submissions", response_model=list[AdminSubmissionResponse])
async def list_submissions(
    status_filter: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(Submission)
    if status_filter:
        query = query.filter(Submission.status == status_filter)
    offset = (page - 1) * limit
    submissions = query.order_by(desc(Submission.created_at)).offset(offset).limit(limit).all()
    result = []
    for s in submissions:
        user = db.query(User).filter(User.id == s.user_id).first()
        problem = db.query(Problem).filter(Problem.id == s.problem_id).first()
        result.append(AdminSubmissionResponse(
            id=s.id, public_id=s.public_id, user_id=s.user_id,
            username=user.username if user else "unknown",
            problem_id=s.problem_id,
            problem_title=problem.title if problem else "Unknown",
            language=s.language, status=s.status,
            runtime_ms=s.runtime_ms, memory_kb=s.memory_kb,
            passed_count=s.passed_count, total_count=s.total_count,
            created_at=s.created_at.isoformat(),
        ))
    return result


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    offset = (page - 1) * limit
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
    result = []
    for log in logs:
        admin_user = db.query(User).filter(User.id == log.admin_id).first()
        result.append(AuditLogResponse(
            id=log.id, admin_id=log.admin_id,
            admin_username=admin_user.username if admin_user else None,
            action=log.action, resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details if log.details else None,
            ip_address=log.ip_address, created_at=log.created_at.isoformat(),
        ))
    return result


@router.post("/problems/generate", response_model=ProblemGenerateResponse, status_code=201)
async def generate_problem(
    body: ProblemGenerateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.ai import ProblemGeneration
    mistral = get_mistral_service()
    generation = ProblemGeneration(
        admin_id=admin.id, prompt=body.prompt, status="pending",
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    try:
        problem_data = await mistral.generate_problem(body.prompt)
        if not problem_data:
            raise Exception("Failed to generate problem data")
        generation.generated_data = json.dumps(problem_data, indent=2)
        generation.status = "completed"
        test_cases_data = problem_data.get("test_cases", [])
        for i, tc in enumerate(test_cases_data):
            gtc = ProblemGenerationTestCase(
                generation_id=generation.id,
                input_data=str(tc.get("input", "")),
                expected_output=str(tc.get("output", "")),
                is_public=True,
                category=tc.get("category", "generated"),
                order_index=i,
            )
            db.add(gtc)
        db.commit()
        db.refresh(generation)
        return ProblemGenerateResponse(
            id=generation.id, prompt=generation.prompt,
            generated_data=generation.generated_data,
            status=generation.status, error_message=None,
            created_at=generation.created_at.isoformat(),
        )
    except Exception as e:
        generation.status = "failed"
        generation.error_message = str(e)
        db.commit()
        return ProblemGenerateResponse(
            id=generation.id, prompt=generation.prompt,
            generated_data="", status=generation.status,
            error_message=generation.error_message,
            created_at=generation.created_at.isoformat(),
        )


@router.get("/generations", response_model=list[dict])
async def list_generations(
    status_filter: str = Query("all"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(ProblemGeneration)
    if status_filter != "all":
        query = query.filter(ProblemGeneration.status == status_filter)
    offset = (page - 1) * limit
    generations = query.order_by(ProblemGeneration.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for g in generations:
        admin_user = db.query(User).filter(User.id == g.admin_id).first()
        test_case_count = db.query(ProblemGenerationTestCase).filter(
            ProblemGenerationTestCase.generation_id == g.id,
        ).count()
        result.append({
            "id": g.id, "admin_id": g.admin_id,
            "admin_username": admin_user.username if admin_user else "unknown",
            "prompt": g.prompt[:200] + ("..." if len(g.prompt) > 200 else ""),
            "status": g.status, "error_message": g.error_message,
            "test_case_count": test_case_count,
            "created_at": g.created_at.isoformat(),
        })
    return result
