"""FastAPI dependency injection utilities."""
from typing import Generator, Optional, Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user, get_current_active_user, require_admin
from app.models.user import User


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Re-export common dependencies for convenience
DbDependency = Annotated[Session, Depends(get_db_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]
ActiveUserDependency = Annotated[User, Depends(get_current_active_user)]
AdminDependency = Annotated[User, Depends(require_admin)]
