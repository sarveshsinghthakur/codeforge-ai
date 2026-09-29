"""Pydantic schemas for problems."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
    is_solved: bool = False
    is_favorite: bool = False

    class Config:
        from_attributes = True


class ProblemListEnvelope(BaseModel):
    """Paginated problem list (also carries per-user flags)."""
    items: List[ProblemListResponse]
    total: int
    page: int
    limit: int


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
    test_cases: List[TestCaseSchema] = Field(default_factory=list)
    hidden_test_case_count: int = 0
    time_limit_ms: int
    memory_limit_mb: int
    created_at: str
    updated_at: str
    is_solved: bool = False
    is_favorite: bool = False

    class Config:
        from_attributes = True


class ProblemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
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

    class Config:
        from_attributes = True


class ProblemQualityReport(BaseModel):
    statement: str  # PASS, WARNING, FAIL
    examples: str
    constraints: str
    starter_code: str
    reference_solution: str
    test_cases: str
    complexity: str
    overall: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TopicProgress(BaseModel):
    topic: str
    solved: int
    attempted: int
    percentage: float


class ProblemSearchParams(BaseModel):
    q: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[str] = None  # solved, unsolved, all
    company: Optional[str] = None
    sort: Optional[str] = Field(None, pattern=r"^(difficulty|acceptance|solved|recent)$")
    order: Optional[str] = Field(default="desc", pattern=r"^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=500)


# Aliases for API imports
ProblemCreate = ProblemCreateRequest
ProblemUpdate = ProblemUpdateRequest
ProblemListParams = ProblemSearchParams
