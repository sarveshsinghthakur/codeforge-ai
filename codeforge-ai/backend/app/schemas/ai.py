"""Schemas for AI assistant, problem generation, test generation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class _ProblemIdModel(BaseModel):
    problem_id: Optional[int] = None

    @field_validator("problem_id", mode="before")
    @classmethod
    def _normalize_problem_id(cls, v):
        # Missing/invalid ids (null, 0, negative) must become NULL so we never
        # insert a non-existent problem_id FK (Postgres rejects it, SQLite didn't).
        if v is None:
            return None
        try:
            iv = int(v)
        except (TypeError, ValueError):
            return None
        return iv if iv > 0 else None


class AIChatRequest(_ProblemIdModel):
    code: Optional[str] = None
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None


class AIChatResponse(BaseModel):
    response: str
    conversation_id: int
    tokens_used: Optional[int] = None


COPILOT_REQUEST_TYPES = (
    "chat",
    "explain_problem",
    "hint",
    "debug",
    "solution",
    "explain_code",
    "complexity",
    "edge_cases",
    "testcases",
    "optimize",
)


class CopilotRequest(_ProblemIdModel):
    request_type: str = Field(default="chat", pattern=r"^(chat|explain_problem|hint|debug|solution|explain_code|complexity|edge_cases|testcases|optimize)$")
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
    code: Optional[str] = Field(None, max_length=100000)
    testcase: Optional[str] = Field(None, max_length=2000)
    conversation_id: Optional[int] = None
    message: Optional[str] = Field(None, max_length=4000)
    hint_level: int = Field(default=1, ge=1, le=3)
    # last run/submit result from the workspace: {status, error_message, test_results}
    run_result: Optional[dict] = None


class CopilotResponse(BaseModel):
    reply: str
    request_type: str
    conversation_id: int
    hint_level: int = 1
    tokens_used: Optional[int] = None


class AIAnalyzeRequest(_ProblemIdModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(default="python", pattern=r"^(python|javascript|java|cpp|c)$")
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


class GeneratedTestCase(BaseModel):
    input_data: str
    expected_output: str
    category: str
    is_edge_case: bool = False


class TestGenerationResponse(BaseModel):
    generated_cases: List[GeneratedTestCase]
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
    complexity: dict = Field(default_factory=dict)
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
