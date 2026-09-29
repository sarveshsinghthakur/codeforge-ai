"""Users API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFound
from app.models.user import User
from app.schemas.auth import UserResponse
import structlog

logger = structlog.get_logger("codeforge")

router = APIRouter()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFound("User")
    return UserResponse(
        id=user.id,
        public_id=user.public_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        is_active=user.is_active,
        preferred_language=user.preferred_language,
        created_at=user.created_at.isoformat(),
    )
