"""Schemas for dashboard, leaderboard, analytics."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from app.schemas.discussion import SubmissionListResponse, ProblemListResponse  # noqa: F401  (forward-ref targets for DashboardResponse)


class DashboardStats(BaseModel):
    problems_solved: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    easy_total: int = 0
    medium_total: int = 0
    hard_total: int = 0
    submission_count: int = 0
    acceptance_rate: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    total_problems_attempted: int = 0
    favorites_count: int = 0


class ActivityPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class TopicProgressItem(BaseModel):
    topic: str
    solved: int
    attempted: int
    percentage: float


class DashboardResponse(BaseModel):
    stats: DashboardStats
    activity_calendar: List[ActivityPoint] = Field(default_factory=list)
    topic_progress: List[TopicProgressItem] = Field(default_factory=list)
    recent_submissions: List["SubmissionListResponse"] = Field(default_factory=list)
    recent_problems: List["ProblemListResponse"] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    problems_solved: int
    rating: int = 0
    weekly_points: int = 0
    monthly_points: int = 0


class LeaderboardResponse(BaseModel):
    period: str  # daily, weekly, monthly, all_time
    entries: List[LeaderboardEntry]
    user_rank: Optional[LeaderboardEntry] = None
    total_users: int


class AnalyticsOverview(BaseModel):
    total_users: int = 0
    active_users_7d: int = 0
    active_users_30d: int = 0
    total_problems: int = 0
    published_problems: int = 0
    total_submissions: int = 0
    accepted_submissions: int = 0
    acceptance_rate: float = 0.0
    total_ai_requests: int = 0


class ProblemStats(BaseModel):
    problem_id: int
    problem_title: str
    problem_slug: str
    difficulty: str
    attempt_count: int
    solved_count: int
    acceptance_rate: float


class LanguageUsage(BaseModel):
    language: str
    count: int
    percentage: float


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    most_attempted: List[ProblemStats] = Field(default_factory=list)
    most_failed: List[ProblemStats] = Field(default_factory=list)
    average_runtime_by_language: dict = Field(default_factory=dict)
    language_usage: List[LanguageUsage] = Field(default_factory=list)
    popular_topics: List[dict] = Field(default_factory=list)
    submission_trend_7d: List[dict] = Field(default_factory=list)
    user_growth_30d: List[dict] = Field(default_factory=list)
