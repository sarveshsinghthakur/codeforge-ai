"""Discussions API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_user
from app.core.exceptions import ProblemNotFound, DiscussionNotFound, NotFound
from app.models.problem import Problem, ProblemStatus
from app.models.discussion import Discussion, Comment
from app.models.user import User
from app.schemas.discussion import (
    DiscussionCreate, DiscussionResponse, CommentCreate, CommentResponse,
    DiscussionDetailResponse,
)

router = APIRouter()


@router.get("/problems/{problem_id}/discussions", response_model=list[DiscussionResponse])
async def list_discussions(
    problem_id: int,
    category: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    problem = db.query(Problem).filter(
        Problem.id == problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()
    query = db.query(Discussion).filter(Discussion.problem_id == problem_id)
    if category:
        query = query.filter(Discussion.category == category)
    discussions = query.order_by(Discussion.created_at.desc()).all()
    return [
        DiscussionResponse(
            id=d.id, public_id=d.public_id, problem_id=d.problem_id, user_id=d.user_id,
            username=d.user.username, display_name=d.user.display_name, avatar_url=d.user.avatar_url,
            title=d.title, content=d.content, category=d.category,
            likes_count=d.likes_count, is_reported=d.is_reported,
            comment_count=len(d.comments),
            created_at=d.created_at.isoformat(), updated_at=d.updated_at.isoformat(),
        )
        for d in discussions
    ]


@router.post("/problems/{problem_id}/discussions", response_model=DiscussionResponse, status_code=201)
async def create_discussion(
    problem_id: int,
    body: DiscussionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    problem = db.query(Problem).filter(
        Problem.id == problem_id,
        Problem.status == ProblemStatus.PUBLISHED.value,
    ).first()
    if not problem:
        raise ProblemNotFound()
    discussion = Discussion(
        problem_id=problem_id, user_id=current_user.id,
        title=body.title, content=body.content, category=body.category,
    )
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    return DiscussionResponse(
        id=discussion.id, public_id=discussion.public_id, problem_id=discussion.problem_id,
        user_id=discussion.user_id, username=current_user.username,
        display_name=current_user.display_name, avatar_url=current_user.avatar_url,
        title=discussion.title, content=discussion.content, category=discussion.category,
        likes_count=discussion.likes_count, is_reported=discussion.is_reported,
        comment_count=0,
        created_at=discussion.created_at.isoformat(), updated_at=discussion.updated_at.isoformat(),
    )


@router.get("/discussions/{discussion_id}", response_model=DiscussionDetailResponse)
async def get_discussion(discussion_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    discussion = db.query(Discussion).filter(Discussion.id == discussion_id).first()
    if not discussion:
        raise DiscussionNotFound()
    return DiscussionDetailResponse(
        id=discussion.id, public_id=discussion.public_id, problem_id=discussion.problem_id,
        user_id=discussion.user_id, username=discussion.user.username,
        display_name=discussion.user.display_name, avatar_url=discussion.user.avatar_url,
        title=discussion.title, content=discussion.content, category=discussion.category,
        likes_count=discussion.likes_count, is_reported=discussion.is_reported,
        comment_count=len(discussion.comments),
        created_at=discussion.created_at.isoformat(), updated_at=discussion.updated_at.isoformat(),
        comments=[
            CommentResponse(
                id=c.id, public_id=c.public_id, discussion_id=c.discussion_id,
                user_id=c.user_id, username=c.user.username,
                display_name=c.user.display_name, avatar_url=c.user.avatar_url,
                content=c.content, likes_count=c.likes_count, is_reported=c.is_reported,
                created_at=c.created_at.isoformat(), updated_at=c.updated_at.isoformat(),
            )
            for c in discussion.comments
        ],
    )


@router.post("/discussions/{discussion_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    discussion_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    discussion = db.query(Discussion).filter(Discussion.id == discussion_id).first()
    if not discussion:
        raise DiscussionNotFound()
    comment = Comment(discussion_id=discussion_id, user_id=current_user.id, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse(
        id=comment.id, public_id=comment.public_id, discussion_id=comment.discussion_id,
        user_id=comment.user_id, username=current_user.username,
        display_name=current_user.display_name, avatar_url=current_user.avatar_url,
        content=comment.content, likes_count=comment.likes_count, is_reported=comment.is_reported,
        created_at=comment.created_at.isoformat(), updated_at=comment.updated_at.isoformat(),
    )


@router.post("/discussions/{discussion_id}/like")
async def like_discussion(discussion_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    discussion = db.query(Discussion).filter(Discussion.id == discussion_id).first()
    if not discussion:
        raise DiscussionNotFound()
    discussion.likes_count += 1
    db.commit()
    return {"message": "Liked", "likes_count": discussion.likes_count}


@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise NotFound("Comment")
    comment.likes_count += 1
    db.commit()
    return {"message": "Liked", "likes_count": comment.likes_count}
