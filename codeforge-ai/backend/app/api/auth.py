"""Auth API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, require_admin, require_user,
)
from app.core.exceptions import Conflict, NotFound, Unauthorized, Forbidden
from app.models.user import User
from app.schemas.auth import UserRegisterRequest as UserRegister, UserLoginRequest as UserLogin, TokenResponse, UserResponse, UserUpdateRequest as UserUpdate, ProfileResponse
from app.models.user_progress import UserProblemProgress
from app.models.submission import Submission
from app.models.problem import Problem

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise Conflict("Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise Conflict("Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=get_password_hash(body.password),
        display_name=body.username,
        role="USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise Unauthorized("Invalid credentials")

    if not user.is_active:
        raise Forbidden("Account is deactivated")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise Unauthorized("Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise Unauthorized("Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise NotFound("User")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_user)):
    return UserResponse(
        id=current_user.id,
        public_id=current_user.public_id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        role=current_user.role,
        is_active=current_user.is_active,
        preferred_language=current_user.preferred_language,
        created_at=current_user.created_at.isoformat(),
    )


@router.put("/auth/me", response_model=UserResponse)
async def update_current_user(body: UserUpdate, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    if body.bio is not None:
        current_user.bio = body.bio
    if body.preferred_language is not None:
        current_user.preferred_language = body.preferred_language
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        public_id=current_user.public_id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        role=current_user.role,
        is_active=current_user.is_active,
        preferred_language=current_user.preferred_language,
        created_at=current_user.created_at.isoformat(),
    )


@router.get("/users/me/dashboard", response_model=ProfileResponse)
async def get_my_dashboard(current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    solved = db.query(UserProblemProgress).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True,
    ).count()

    submissions = db.query(Submission).filter(Submission.user_id == current_user.id).all()
    accepted = len([s for s in submissions if s.status == "accepted"])
    total = len(submissions)
    acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

    easy_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True,
        Problem.difficulty == "easy",
    ).count()

    medium_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True,
        Problem.difficulty == "medium",
    ).count()

    hard_solved = db.query(UserProblemProgress).join(Problem).filter(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.solved == True,
        Problem.difficulty == "hard",
    ).count()

    return ProfileResponse(
        id=current_user.id,
        public_id=current_user.public_id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        role=current_user.role,
        is_active=current_user.is_active,
        preferred_language=current_user.preferred_language,
        created_at=current_user.created_at.isoformat(),
        problems_solved=solved,
        easy_solved=easy_solved,
        medium_solved=medium_solved,
        hard_solved=hard_solved,
        submission_count=total,
        acceptance_rate=round(acceptance_rate, 1),
    )
