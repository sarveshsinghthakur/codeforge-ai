"""Problem model."""
import uuid
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProblemStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0)
    solved_count: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    topics: Mapped[str] = mapped_column(Text, default="[]")
    constraints: Mapped[str] = mapped_column(Text, default="[]")
    examples: Mapped[str] = mapped_column(Text, default="[]")
    hints: Mapped[str] = mapped_column(Text, default="[]")
    follow_up: Mapped[str] = mapped_column(Text, nullable=True)
    starter_code: Mapped[str] = mapped_column(Text, default="{}")
    reference_solution: Mapped[str] = mapped_column(Text, nullable=True)
    solution_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    complexity_time: Mapped[str] = mapped_column(String(50), nullable=True)
    complexity_space: Mapped[str] = mapped_column(String(50), nullable=True)
    company: Mapped[str] = mapped_column(String(100), nullable=True)
    related_problems: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem")
    progress = relationship("UserProblemProgress", back_populates="problem", cascade="all, delete-orphan")
    discussions = relationship("Discussion", back_populates="problem")

    def __repr__(self):
        return f"<Problem {self.slug}>"
