"""Premium access checks shared by problem and submission APIs."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import UserSubscription, utcnow_naive

LOCKED_DIFFICULTIES = {"medium", "hard"}


def has_premium(db: Session, user: Optional[object]) -> bool:
    """True when the user may access Medium/Hard problems."""
    if user is None:
        return False
    if getattr(user, "role", None) == "ADMIN":
        return True
    now = utcnow_naive()
    return (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == getattr(user, "id", -1),
            UserSubscription.status == "active",
            UserSubscription.expires_at > now,
        )
        .count()
        > 0
    )


def is_locked(problem, premium: bool) -> bool:
    return (not premium) and getattr(problem, "difficulty", None) in LOCKED_DIFFICULTIES
