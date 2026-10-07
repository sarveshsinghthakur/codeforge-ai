"""User progress model."""
from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserProblemProgress(Base):
    __tablename__ = "user_problem_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    solved: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    solved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_language: Mapped[str] = mapped_column(String(20), nullable=True)
    current_streak_day: Mapped[str] = mapped_column(String(10), nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="progress")
    problem = relationship("Problem", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem"),
    )

    def __repr__(self):
        return f"<UserProblemProgress user={self.user_id} problem={self.problem_id}>"
