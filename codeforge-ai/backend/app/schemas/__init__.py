"""Pydantic schemas for auth, users, problems, submissions, AI, admin, analytics, discussions, contests."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_lower(cls, v: str) -> str:
        return v.lower()


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    public_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: str
    is_active: bool
    preferred_language: str
    created_at: str

    model_config = {"from_attributes": True}


class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=500)
    preferred_language: Optional[str] = Field(None, pattern=r"^(python|javascript|java|cpp|c)$")


class UserSettingsResponse(BaseModel):
    preferred_language: str
    editor_font_size: int = 14
    editor_word_wrap: bool = True
    editor_minimap: bool = True
    editor_theme: str = "dark"
    notifications_enabled: bool = True


class UserSettingsUpdateRequest(BaseModel):
    preferred_language: Optional[str] = Field(None, pattern=r"^(python|javascript|java|cpp|c)$")
    editor_font_size: Optional[int] = Field(None, ge=10, le=30)
    editor_word_wrap: Optional[bool] = None
    editor_minimap: Optional[bool] = None
    editor_theme: Optional[str] = Field(None, pattern=r"^(dark|light)$")
    notifications_enabled: Optional[bool] = None


# ── Problems ──────────────────────────────────────────────────────────────────

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

    model_config = {"from_attributes": True}


class TestCaseSchema(BaseModel):
    id: Optional[int] = None
    input_data: str
    expected_output: str
    is_public: bool = False
    is_edge_case: bool = False
    edge_case_category: Optional[str] = None
    order_index: int = 0


class ProblemDetailResponse(BaseModel):
    id: int
    public_id: str
    title: str
    slug: str
    difficulty: str
    acceptance_rate: float
    solved_count: int
    attempt_count: int
    description: str
    topics: List[str]
    constraints: List[str]
    examples: List[dict]
    hints: List[str]
    follow_up: Optional[str] = None
    starter_code: dict
    solution_explanation: Optional[str] = None
    complexity_time: Optional[str] = None
    complexity_space: Optional[str] = None
    company: Optional[str] = None
    related_problems: List[str]
    time_limit_ms: int
    memory_limit_mb: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProblemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    difficulty: str = Field(..., pattern=r"^(easy|medium|hard)$")
    description: str = Field(..., min_length=1)
    topics: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    examples: List[dict] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)
    follow_up: Optional[str] = None
    starter_code: dict = Field(default_factory=dict)
    reference_solution: Optional[str] = None
    solution_explanation: Optional[str] = None
    complexity_time: Optional[str] = None
    complexity_space: Optional[str] = None
    company: Optional[str] = None
    related_problems: List[str] = Field(default_factory=list)
    time_limit_ms: int = Field(default=1000, ge=100, le=30000)
    memory_limit_mb: int = Field(default=256, ge=64, le=1024)


class ProblemUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    difficulty: Optional[str] = Field(None, pattern=r"^(easy|medium|hard)$")
    description: Optional[str] = Field(None, min_length=1)
    topics: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    examples: Optional[List[dict]] = None
    hints: Optional[List[str]] = None
    follow_up: Optional[str] = None
    starter_code: Optional[dict] = None
    reference_solution: Optional[str] = None
    solution_explanation: Optional[str] = None
    complexity_time: Optional[str] = None
    complexity_space: Optional[str] = None
    company: Optional[str] = None
    related_problems: Optional[List[str]] = None
    time_limit_ms: Optional[int] = Field(None, ge=100, le=30000)
    memory_limit_mb: Optional[int] = Field(None, ge=64, le=1024)
    status: Optional[str] = Field(None, pattern=r"^(draft|review|published|archived)$")


class ProblemGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000)


class ProblemGenerateResponse(BaseModel):
    id: int
    prompt: str
    generated_data: str
    status: str
    error_message: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class ProblemQualityReport(BaseModel):
    statement: str
    examples: str
    constraints: str
    starter_code: str
    reference_solution: str
    test_cases: str
    complexity: str
    overall: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TopicProgressItem(BaseModel):
    topic: str
    solved: int
    attempted: int
    percentage: float


class ProblemSearchParams(BaseModel):
    q: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[str] = None
    company: Optional[str] = None
    sort: Optional[str] = Field(None, pattern=r"^(difficulty|acceptance|solved|recent)$")
    order: Optional[str] = Field(default="desc", pattern=r"^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class ProblemListRequest(BaseModel):
    q: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[str] = None
    company: Optional[str] = None
    sort: Optional[str] = None
    order: Optional[str] = "desc"
    page: int = 1
    limit: int = 20


# ── Submissions ───────────────────────────────────────────────────────────────

class SubmissionCreateRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    language: str = Field(..., pattern=r"^(python|javascript|java|cpp|c)$")
    source_code: str = Field(..., min_length=1, max_length=100000)


class TestResultSchema(BaseModel):
    test_number: int
    input_data: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: bool
    is_public: bool = True


class SubmissionResultResponse(BaseModel):
    id: int
    public_id: str
    problem_id: int
    language: str
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    passed_count: int = 0
    total_count: int = 0
    test_results: List[TestResultSchema] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


class SubmissionDetailResponse(SubmissionListResponse):
    source_code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    passed_count: int = 0
    total_count: int = 0
    test_results: List[TestResultSchema] = Field(default_factory=list)


# ── AI ────────────────────────────────────────────────────────────────────────

class AIChatRequest(BaseModel):
    problem_id: Optional[int] = None
    code: Optional[str] = None
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None


class AIChatResponse(BaseModel):
    response: str
    conversation_id: int
    tokens_used: Optional[int] = None


class AIAnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
    problem_id: Optional[int] = None
    analysis_type: str = Field(
        default="analyze",
        pattern=r"^(analyze|bugs|complexity|optimize|explain|edge_cases|explain_error)$"
    )


class AIAnalyzeResponse(BaseModel):
    analysis: str
    suggestions: List[str] = Field(default_factory=list)
    complexity: Optional[dict] = None
    potential_bugs: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)


class HintRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    code: Optional[str] = None
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
    hint_level: int = Field(default=1, ge=1, le=3)


class HintResponse(BaseModel):
    problem_id: int
    hint_level: int
    hint: str
    solution_revealed: bool = False


class TestGenerationRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    reference_solution: str = Field(..., min_length=1)
    count: int = Field(default=10, ge=1, le=50)
    categories: List[str] = Field(default_factory=list)


class GeneratedTestCaseSchema(BaseModel):
    input_data: str
    expected_output: str
    category: str
    is_edge_case: bool = False


class TestGenerationResponse(BaseModel):
    generated_cases: List[GeneratedTestCaseSchema]
    verified_count: int
    failed_verification: int
    duplicate_count: int
    warnings: List[str] = Field(default_factory=list)


class ProblemGenerationData(BaseModel):
    title: str
    slug: str
    difficulty: str
    description: str
    constraints: List[str]
    examples: List[dict]
    topics: List[str]
    hints: List[str]
    follow_up: Optional[str] = None
    starter_code: dict
    solution_explanation: Optional[str] = None
    complexity_time: Optional[str] = None
    complexity_space: Optional[str] = None
    test_cases: List[dict] = Field(default_factory=list)
    reference_solution: Optional[str] = None
    company: Optional[str] = None


class TestVerifyRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    input_data: str
    expected_output: str
    reference_solution: str
    language: str = "python"


class TestVerifyResponse(BaseModel):
    verified: bool
    actual_output: Optional[str] = None
    match: bool = False
    error: Optional[str] = None


# ── Users / Dashboard / Leaderboard ──────────────────────────────────────────

class DashboardStats(BaseModel):
    problems_solved: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    submission_count: int = 0
    acceptance_rate: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    total_problems_attempted: int = 0


class ActivityPoint(BaseModel):
    date: str
    count: int


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
    period: str
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


class ProblemStatsItem(BaseModel):
    problem_id: int
    problem_title: str
    problem_slug: str
    difficulty: str
    attempt_count: int
    solved_count: int
    acceptance_rate: float


class LanguageUsageItem(BaseModel):
    language: str
    count: int
    percentage: float


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    most_attempted: List[ProblemStatsItem] = Field(default_factory=list)
    most_failed: List[ProblemStatsItem] = Field(default_factory=list)
    average_runtime_by_language: dict = Field(default_factory=dict)
    language_usage: List[LanguageUsageItem] = Field(default_factory=list)
    popular_topics: List[dict] = Field(default_factory=list)
    submission_trend_7d: List[dict] = Field(default_factory=list)
    user_growth_30d: List[dict] = Field(default_factory=list)


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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


# ── API Success/Error wrappers ────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
