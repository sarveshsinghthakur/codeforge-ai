"""Pydantic schemas for submissions and code execution."""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class SubmissionCreateRequest(BaseModel):
    problem_id: int = Field(..., gt=0)
    language: str = Field(..., pattern=r"^(python|javascript|java|cpp|c)$")
    source_code: str = Field(..., min_length=1, max_length=100000)
    # run     -> public test cases only, not persisted (quick feedback loop)
    # submit  -> all test cases, persisted, affects stats/progress
    # custom  -> a single user-provided input, not persisted
    mode: Literal["run", "submit", "custom"] = "submit"
    custom_input: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Input for mode='custom', in the same format as test-case inputs",
    )


class SubmissionResult(BaseModel):
    id: Optional[int] = None
    public_id: Optional[str] = None
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
    created_at: str
    mode: str = "submit"
    test_results: List["TestResult"] = Field(default_factory=list)


class TestResult(BaseModel):
    test_number: int
    input_data: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: bool
    is_public: bool = True


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


class SubmissionDetailResponse(SubmissionListResponse):
    source_code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    passed_count: int = 0
    total_count: int = 0
    test_results: List[TestResult] = Field(default_factory=list)


class ExecutionRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(..., pattern=r"^(python|javascript|java|cpp|c)$")
    test_cases: List[dict] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    test_results: List[TestResult] = Field(default_factory=list)
    total_passed: int = 0
    total_failed: int = 0


# Alias for API imports
SubmissionCreate = SubmissionCreateRequest
