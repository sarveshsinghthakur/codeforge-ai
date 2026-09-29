"""Analytics API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.security import require_admin, require_user
from app.models.user import User
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission
from app.models.ai import AIMessage
from app.models.user_progress import UserProblemProgress
from app.schemas.discussion import AnalyticsOverview, ProblemStats, LanguageUsage

router = APIRouter()


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def analytics_overview(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
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
    return AnalyticsOverview(
        total_users=total_users, active_users_7d=active_7d, active_users_30d=active_30d,
        total_problems=total_problems, published_problems=published_problems,
        total_submissions=total_submissions, accepted_submissions=accepted_submissions,
        acceptance_rate=acceptance_rate, total_ai_requests=total_ai_requests,
    )


@router.get("/analytics/most-attempted", response_model=list[ProblemStats])
async def most_attempted(limit: int = 10, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    problems = db.query(
        Problem.id, Problem.title, Problem.slug, Problem.difficulty,
        Problem.attempt_count, Problem.solved_count,
    ).order_by(Problem.attempt_count.desc()).limit(limit).all()
    result = []
    for p in problems:
        total = db.query(Submission).filter(Submission.problem_id == p.id).count()
        accepted = db.query(Submission).filter(
            Submission.problem_id == p.id, Submission.status == "accepted",
        ).count()
        acc_rate = round(accepted / total * 100, 1) if total > 0 else 0.0
        result.append(ProblemStats(
            problem_id=p.id, problem_title=p.title, problem_slug=p.slug,
            difficulty=p.difficulty, attempt_count=p.attempt_count,
            solved_count=p.solved_count, acceptance_rate=acc_rate,
        ))
    return result


@router.get("/analytics/most-failed", response_model=list[ProblemStats])
async def most_failed(limit: int = 10, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    failures = db.query(
        Problem.id, Problem.title, Problem.slug, Problem.difficulty,
        func.count(Submission.id).label("failures"),
    ).join(Submission, Submission.problem_id == Problem.id).filter(
        Submission.status != "accepted",
    ).group_by(Problem.id).order_by(func.count(Submission.id).desc()).limit(limit).all()
    return [
        ProblemStats(
            problem_id=f.id, problem_title=f.title, problem_slug=f.slug,
            difficulty=f.difficulty, attempt_count=0, solved_count=0, acceptance_rate=0.0,
        )
        for f in failures
    ]


@router.get("/analytics/language-usage", response_model=list[LanguageUsage])
async def language_usage(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    results = db.query(
        Submission.language, func.count(Submission.id).label("count"),
    ).group_by(Submission.language).all()
    total = sum(r.count for r in results)
    return [
        LanguageUsage(language=r.language, count=r.count,
                      percentage=round(r.count / total * 100, 1) if total > 0 else 0.0)
        for r in results
    ]


@router.get("/analytics/leaderboard")
async def leaderboard(
    period: str = Query("all", pattern="^(all|week|month)$"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Public leaderboard endpoint."""
    since = None
    if period == "week":
        since = datetime.now(timezone.utc) - timedelta(days=7)
    elif period == "month":
        since = datetime.now(timezone.utc) - timedelta(days=30)

    subquery = db.query(
        UserProblemProgress.user_id,
        func.sum(func.cast(UserProblemProgress.solved, func.Integer)).label("solved"),
        func.sum(func.case((UserProblemProgress.solved == True, 1), else_=0)).filter(
            Problem.difficulty == "easy"
        ).label("easy_solved"),
    ).join(Problem).subquery()

    # Simple version - get all users with solved counts
    users = db.query(
        User.id,
        User.username,
        User.display_name,
    ).filter(User.is_active == True).all()

    result = []
    for u in users:
        solved_q = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == u.id,
            UserProblemProgress.solved == True,
        )
        if since:
            solved_q = solved_q.filter(UserProblemProgress.solved_at >= since)
        solved = solved_q.count()

        easy_solved = db.query(UserProblemProgress).join(Problem).filter(
            UserProblemProgress.user_id == u.id,
            UserProblemProgress.solved == True,
            Problem.difficulty == "easy",
        ).count()

        medium_solved = db.query(UserProblemProgress).join(Problem).filter(
            UserProblemProgress.user_id == u.id,
            UserProblemProgress.solved == True,
            Problem.difficulty == "medium",
        ).count()

        hard_solved = db.query(UserProblemProgress).join(Problem).filter(
            UserProblemProgress.user_id == u.id,
            UserProblemProgress.solved == True,
            Problem.difficulty == "hard",
        ).count()

        submissions = db.query(Submission).filter(
            Submission.user_id == u.id,
        )
        if since:
            submissions = submissions.filter(Submission.created_at >= since)
        total_subs = submissions.count()

        accepted_subs = submissions.filter(Submission.status == "accepted").count()
        acceptance = round(accepted_subs / total_subs * 100, 1) if total_subs > 0 else 0.0

        result.append({
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "problems_solved": solved,
            "easy_solved": easy_solved,
            "medium_solved": medium_solved,
            "hard_solved": hard_solved,
            "submission_count": total_subs,
            "acceptance_rate": acceptance,
        })

    result.sort(key=lambda x: (-x["problems_solved"], -x["acceptance_rate"]))
    return result[:limit]
