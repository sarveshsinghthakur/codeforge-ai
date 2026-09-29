"""Contests API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import require_user
from app.core.exceptions import NotFound, Unauthorized
from app.models.contest import Contest, ContestStatus, ContestParticipant, ContestProblem
from app.models.problem import Problem
from app.models.user import User
from app.schemas.discussion import (
    ContestCreate, ContestResponse, ContestDetailResponse, ContestProblemItem,
    ContestJoinRequest, ContestParticipantResponse, ContestLeaderboardEntry, ContestLeaderboardResponse,
)

router = APIRouter()


@router.get("/contests", response_model=list[ContestResponse])
async def list_contests(
    status_filter: str = Query("active"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    query = db.query(Contest)
    if status_filter == "upcoming":
        query = query.filter(Contest.status == ContestStatus.UPCOMING.value)
    elif status_filter == "active":
        query = query.filter(Contest.status == ContestStatus.ACTIVE.value)
    elif status_filter == "ended":
        query = query.filter(Contest.status == ContestStatus.ENDED.value)
    elif status_filter == "draft":
        query = query.filter(Contest.status == ContestStatus.DRAFT.value)
    contests = query.order_by(desc(Contest.created_at)).all()
    now = datetime.now(timezone.utc)
    result = []
    for c in contests:
        participant_count = db.query(ContestParticipant).filter(ContestParticipant.contest_id == c.id).count()
        problems_count = db.query(ContestProblem).filter(ContestProblem.contest_id == c.id).count()
        computed_status = c.status
        if c.status == ContestStatus.UPCOMING.value and c.start_time and c.start_time <= now:
            computed_status = ContestStatus.ACTIVE.value
        elif c.status == ContestStatus.ACTIVE.value and c.end_time and c.end_time < now:
            computed_status = ContestStatus.ENDED.value
        result.append(ContestResponse(
            id=c.id, public_id=c.public_id, title=c.title, description=c.description,
            contest_type=c.contest_type, status=computed_status,
            start_time=c.start_time.isoformat() if c.start_time else None,
            end_time=c.end_time.isoformat() if c.end_time else None,
            duration_minutes=c.duration_minutes, max_participants=c.max_participants,
            participant_count=participant_count, problems_count=problems_count,
            created_at=c.created_at.isoformat(),
        ))
    return result


@router.get("/contests/{contest_id}", response_model=ContestDetailResponse)
async def get_contest(contest_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise NotFound("Contest")
    contest_problems = db.query(ContestProblem).filter(ContestProblem.contest_id == contest_id).order_by(ContestProblem.order_index).all()
    problems_data = []
    for cp in contest_problems:
        problem = db.query(Problem).filter(Problem.id == cp.problem_id).first()
        if problem:
            problems_data.append(ContestProblemItem(
                id=cp.id, problem_id=problem.id, problem_title=problem.title,
                problem_slug=problem.slug, difficulty=problem.difficulty,
                order_index=cp.order_index, points=cp.points,
            ))
    participation = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == current_user.id,
    ).first()
    my_participation = None
    if participation:
        my_participation = {
            "contest_id": participation.contest_id, "user_id": participation.user_id,
            "score": participation.score, "penalty_seconds": participation.penalty_seconds,
            "submission_count": participation.submission_count,
            "problems_solved": participation.problems_solved,
            "joined_at": participation.joined_at.isoformat(),
            "completed_at": participation.completed_at.isoformat() if participation.completed_at else None,
        }
    return ContestDetailResponse(
        id=contest.id, public_id=contest.public_id, title=contest.title,
        description=contest.description, contest_type=contest.contest_type,
        status=contest.status,
        start_time=contest.start_time.isoformat() if contest.start_time else None,
        end_time=contest.end_time.isoformat() if contest.end_time else None,
        duration_minutes=contest.duration_minutes, max_participants=contest.max_participants,
        participant_count=db.query(ContestParticipant).filter(ContestParticipant.contest_id == contest_id).count(),
        problems_count=len(problems_data), created_at=contest.created_at.isoformat(),
        problems=problems_data, my_participation=my_participation,
    )


@router.post("/contests/{contest_id}/join", response_model=ContestParticipantResponse, status_code=201)
async def join_contest(contest_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise NotFound("Contest")
    if contest.status == ContestStatus.DRAFT.value:
        raise Unauthorized("Contest is not open for registration")
    existing = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == current_user.id,
    ).first()
    if existing:
        raise Unauthorized("Already joined this contest")
    if contest.max_participants:
        count = db.query(ContestParticipant).filter(ContestParticipant.contest_id == contest_id).count()
        if count >= contest.max_participants:
            raise Unauthorized("Contest is full")
    participant = ContestParticipant(contest_id=contest_id, user_id=current_user.id)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return ContestParticipantResponse(
        contest_id=participant.contest_id, user_id=participant.user_id,
        score=participant.score, penalty_seconds=participant.penalty_seconds,
        submission_count=participant.submission_count,
        problems_solved=participant.problems_solved,
        joined_at=participant.joined_at.isoformat(),
        completed_at=participant.completed_at.isoformat() if participant.completed_at else None,
    )
