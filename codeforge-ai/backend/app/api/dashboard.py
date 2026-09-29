"""Dashboard and leaderboard API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from app.core.database import get_db
from app.core.security import require_user
from app.models.user import User
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission
from app.models.user_progress import UserProblemProgress
from app.models.favorite import UserFavorite
from app.schemas.discussion import (
    LeaderboardEntry,
    LeaderboardResponse,
    DashboardResponse,
    DashboardStats,
    ActivityPoint,
)
import json

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    today = datetime.now(timezone.utc).date()
    progress_list = db.query(UserProblemProgress).filter(
        UserProblemProgress.user_id == current_user.id,
    ).all()
    solved_count = len([p for p in progress_list if p.solved])
    attempt_count = len(progress_list)

    easy_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True, Problem.difficulty == "easy",
    ).count()

    medium_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True, Problem.difficulty == "medium",
    ).count()

    hard_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True, Problem.difficulty == "hard",
    ).count()

    submissions = db.query(Submission).filter(Submission.user_id == current_user.id).all()
    total_subs = len(submissions)
    accepted_subs = len([s for s in submissions if s.status == "accepted"])
    acceptance_rate = round(accepted_subs / total_subs * 100, 1) if total_subs > 0 else 0.0

    # Current streak
    current_streak = 0
    streak_day = today
    while True:
        has_activity = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == current_user.id,
            func.date(UserProblemProgress.last_attempt_at) == streak_day,
        ).first()
        if has_activity:
            current_streak += 1
            streak_day -= timedelta(days=1)
        else:
            break

    # Longest streak
    longest_streak = 0
    streak_start = None
    current = 0
    for p in sorted(progress_list, key=lambda x: x.last_attempt_at or datetime.min):
        if p.last_attempt_at:
            attempt_date = p.last_attempt_at.date()
            if streak_start is None:
                streak_start = attempt_date
                current = 1
            elif (attempt_date - streak_start).days == current:
                current += 1
                streak_start = attempt_date
            else:
                longest_streak = max(longest_streak, current)
                streak_start = attempt_date
                current = 1
    longest_streak = max(longest_streak, current)

    # Activity calendar (last 365 days)
    activity_calendar = []
    for i in range(365):
        day = today - timedelta(days=364 - i)
        day_str = day.isoformat()
        count = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == current_user.id,
            func.date(UserProblemProgress.last_attempt_at) == day,
        ).count()
        if count > 0:
            activity_calendar.append(ActivityPoint(date=day_str, count=min(count, 5)))

    # Topic progress
    topic_progress = {}
    for p in progress_list:
        if p.solved and p.problem:
            problem = p.problem
            topics = json.loads(problem.topics) if problem.topics else []
            for topic in topics:
                if topic not in topic_progress:
                    topic_progress[topic] = {"solved": 0, "attempted": 0}
                topic_progress[topic]["solved"] += 1
    for s in submissions:
        problem = db.query(Problem).filter(Problem.id == s.problem_id).first()
        if problem:
            topics = json.loads(problem.topics) if problem.topics else []
            for topic in topics:
                if topic not in topic_progress:
                    topic_progress[topic] = {"solved": 0, "attempted": 0}
                topic_progress[topic]["attempted"] += 1

    topic_list = [
        {"topic": t, "solved": d["solved"], "attempted": d["attempted"],
         "percentage": round(d["solved"] / d["attempted"] * 100, 1) if d["attempted"] > 0 else 0.0}
        for t, d in sorted(topic_progress.items(), key=lambda x: x[1]["solved"], reverse=True)[:10]
    ]

    # Recent submissions
    recent_submissions = db.query(Submission).filter(
        Submission.user_id == current_user.id,
    ).order_by(desc(Submission.created_at)).limit(10).all()

    recent_subs_data = []
    for s in recent_submissions:
        problem = db.query(Problem).filter(Problem.id == s.problem_id).first()
        recent_subs_data.append({
            "id": s.id, "public_id": s.public_id, "problem_id": s.problem_id,
            "problem_title": problem.title if problem else "Unknown",
            "problem_slug": problem.slug if problem else "",
            "language": s.language, "status": s.status,
            "runtime_ms": s.runtime_ms, "memory_kb": s.memory_kb,
            "created_at": s.created_at.isoformat(),
        })

    # Recent problems
    recent_problems = db.query(Problem).filter(
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).order_by(desc(Problem.created_at)).limit(10).all()

    recent_problems_data = []
    for p in recent_problems:
        recent_problems_data.append({
            "id": p.id, "public_id": p.public_id, "title": p.title, "slug": p.slug,
            "difficulty": p.difficulty, "acceptance_rate": p.acceptance_rate,
            "solved_count": p.solved_count, "attempt_count": p.attempt_count,
            "topics": json.loads(p.topics) if p.topics else [],
            "company": p.company, "created_at": p.created_at.isoformat(),
        })

    # Denominators per difficulty + favorites count
    totals = {
        row[0]: row[1]
        for row in db.query(Problem.difficulty, func.count(Problem.id))
        .filter(Problem.status == ProblemStatus.PUBLISHED.value)
        .group_by(Problem.difficulty)
        .all()
    }
    favorites_count = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id
    ).count()

    return DashboardResponse(
        stats=DashboardStats(
            problems_solved=solved_count, easy_solved=easy_solved,
            medium_solved=medium_solved, hard_solved=hard_solved,
            easy_total=totals.get("easy", 0),
            medium_total=totals.get("medium", 0),
            hard_total=totals.get("hard", 0),
            submission_count=total_subs, acceptance_rate=acceptance_rate,
            current_streak=current_streak, longest_streak=longest_streak,
            total_problems_attempted=attempt_count,
            favorites_count=favorites_count,
        ),
        activity_calendar=activity_calendar,
        topic_progress=topic_list,
        recent_submissions=recent_subs_data,
        recent_problems=recent_problems_data,
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    period: str = Query("all_time", description="daily, weekly, monthly, all_time"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    subquery = db.query(
        UserProblemProgress.user_id,
        func.count(UserProblemProgress.id).label("solved_count"),
    ).filter(UserProblemProgress.solved == True).group_by(UserProblemProgress.user_id).subquery()

    users = db.query(
        User, subquery.c.solved_count,
    ).outerjoin(subquery, User.id == subquery.c.user_id).order_by(
        desc(subquery.c.solved_count), desc(User.created_at),
    ).limit(limit).all()

    entries = []
    user_rank = None
    for rank, (user, solved_count) in enumerate(users, 1):
        entry = LeaderboardEntry(
            rank=rank, user_id=user.id, username=user.username,
            display_name=user.display_name, avatar_url=user.avatar_url,
            problems_solved=solved_count or 0, rating=0, weekly_points=0, monthly_points=0,
        )
        entries.append(entry)
        if user.id == current_user.id:
            user_rank = entry

    return LeaderboardResponse(
        period=period, entries=entries, user_rank=user_rank,
        total_users=db.query(User).count(),
    )
