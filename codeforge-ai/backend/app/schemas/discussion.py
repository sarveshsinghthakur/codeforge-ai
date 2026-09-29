"""Schemas for discussions, contests, admin, dashboard — re-exported for convenience."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Discussions ───────────────────────────────────────────────────────────────

class DiscussionCreateRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    category: str = Field(default="question", pattern=r"^(solution|hint|approach|question|optimization)$")


class DiscussionResponse(BaseModel):
    id: int
    public_id: str
    problem_id: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    title: str
    content: str
    category: str
    likes_count: int = 0
    is_reported: bool = False
    comment_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CommentCreateRequest(BaseModel):
    discussion_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(BaseModel):
    id: int
    public_id: str
    discussion_id: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    content: str
    likes_count: int = 0
    is_reported: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DiscussionDetailResponse(DiscussionResponse):
    comments: List[CommentResponse] = Field(default_factory=list)


# ── Contests ──────────────────────────────────────────────────────────────────

class ContestCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contest_type: str = Field(default="practice", pattern=r"^(practice|ranked|custom)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    max_participants: Optional[int] = Field(None, gt=0)
    problem_ids: List[int] = Field(default_factory=list)


class ContestProblemItem(BaseModel):
    id: int
    problem_id: int
    problem_title: str
    problem_slug: str
    difficulty: str
    order_index: int
    points: int

    class Config:
        from_attributes = True


class ContestResponse(BaseModel):
    id: int
    public_id: str
    title: str
    description: Optional[str] = None
    contest_type: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    max_participants: Optional[int] = None
    participant_count: int = 0
    problems_count: int = 0
    created_at: str

    class Config:
        from_attributes = True


class ContestDetailResponse(ContestResponse):
    problems: List[ContestProblemItem] = Field(default_factory=list)
    my_participation: Optional[dict] = None


class ContestJoinRequest(BaseModel):
    pass


class ContestParticipantResponse(BaseModel):
    contest_id: int
    user_id: int
    score: int = 0
    penalty_seconds: int = 0
    submission_count: int = 0
    problems_solved: int = 0
    joined_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class ContestLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    score: int = 0
    penalty_seconds: int = 0
    problems_solved: int = 0
    submission_count: int = 0


class ContestLeaderboardResponse(BaseModel):
    contest_id: int
    entries: List[ContestLeaderboardEntry]
    user_entry: Optional[ContestLeaderboardEntry] = None


# ── Dashboard / Leaderboard ──────────────────────────────────────────────────

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
    date: str
    count: int


class TopicProgressItem(BaseModel):
    topic: str
    solved: int
    attempted: int
    percentage: float


class ProblemListResponse(BaseModel):
    id: int
    public_id: str
    title: str
    slug: str
    difficulty: str
    acceptance_rate: float
    solved_count: int
    attempt_count: int
    topics: List[str]
    company: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    id: int
    public_id: str
    problem_id: int
    problem_title: str
    problem_slug: str
    language: str
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    stats: DashboardStats
    activity_calendar: List[ActivityPoint] = Field(default_factory=list)
    topic_progress: List[TopicProgressItem] = Field(default_factory=list)
    recent_submissions: List[SubmissionListResponse] = Field(default_factory=list)
    recent_problems: List[ProblemListResponse] = Field(default_factory=list)


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
    period: str
    entries: List[LeaderboardEntry]
    user_rank: Optional[LeaderboardEntry] = None
    total_users: int


# ── Analytics ─────────────────────────────────────────────────────────────────

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


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminUserResponse(BaseModel):
    id: int
    public_id: str
    username: str
    email: str
    role: str
    is_active: bool
    problems_solved: int = 0
    submission_count: int = 0
    joined_at: str

    class Config:
        from_attributes = True


class AdminSubmissionResponse(BaseModel):
    id: int
    public_id: str
    user_id: int
    username: str
    problem_id: int
    problem_title: str
    language: str
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    passed_count: int = 0
    total_count: int = 0
    created_at: str

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    admin_id: Optional[int] = None
    admin_username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# ── Aliases for API imports ───────────────────────────────────────────────────
DiscussionCreate = DiscussionCreateRequest
CommentCreate = CommentCreateRequest
ContestCreate = ContestCreateRequest
