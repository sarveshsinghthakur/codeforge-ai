"""Test cases API routes (admin only)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.core.exceptions import ProblemNotFound, NotFound
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.problem import TestCaseSchema
from app.services.code_execution import CodeExecutionService, get_execution_service

router = APIRouter()


@router.get("/admin/problems/{problem_id}/test-cases", response_model=list[TestCaseSchema])
async def list_test_cases(problem_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ProblemNotFound()
    test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).order_by(TestCase.order_index).all()
    return [
        TestCaseSchema(
            id=tc.id, input_data=tc.input_data, expected_output=tc.expected_output,
            is_public=tc.is_public, is_edge_case=tc.is_edge_case,
            edge_case_category=tc.edge_case_category, order_index=tc.order_index,
        )
        for tc in test_cases
    ]


@router.post("/admin/problems/{problem_id}/test-cases", response_model=TestCaseSchema, status_code=201)
async def create_test_case(
    problem_id: int,
    body: TestCaseSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ProblemNotFound()
    max_order = db.query(TestCase).filter(TestCase.problem_id == problem_id).count()
    tc = TestCase(
        problem_id=problem_id, input_data=body.input_data, expected_output=body.expected_output,
        is_public=body.is_public, is_edge_case=body.is_edge_case,
        edge_case_category=body.edge_case_category,
        order_index=body.order_index if body.order_index is not None else max_order,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return TestCaseSchema(
        id=tc.id, input_data=tc.input_data, expected_output=tc.expected_output,
        is_public=tc.is_public, is_edge_case=tc.is_edge_case,
        edge_case_category=tc.edge_case_category, order_index=tc.order_index,
    )


@router.put("/admin/test-cases/{test_case_id}", response_model=TestCaseSchema)
async def update_test_case(
    test_case_id: int,
    body: TestCaseSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    tc = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not tc:
        raise NotFound("Test case")
    tc.input_data = body.input_data
    tc.expected_output = body.expected_output
    tc.is_public = body.is_public
    tc.is_edge_case = body.is_edge_case
    tc.edge_case_category = body.edge_case_category
    if body.order_index is not None:
        tc.order_index = body.order_index
    db.commit()
    db.refresh(tc)
    return TestCaseSchema(
        id=tc.id, input_data=tc.input_data, expected_output=tc.expected_output,
        is_public=tc.is_public, is_edge_case=tc.is_edge_case,
        edge_case_category=tc.edge_case_category, order_index=tc.order_index,
    )


@router.delete("/admin/test-cases/{test_case_id}")
async def delete_test_case(test_case_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    tc = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not tc:
        raise NotFound("Test case")
    problem_id = tc.problem_id
    db.delete(tc)
    remaining = db.query(TestCase).filter(TestCase.problem_id == problem_id).order_by(TestCase.order_index).all()
    for i, rt in enumerate(remaining):
        rt.order_index = i
    db.commit()
    return {"message": "Test case deleted"}


@router.post("/admin/test-cases/{test_case_id}/verify")
async def verify_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    tc = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not tc:
        raise NotFound("Test case")
    problem = db.query(Problem).filter(Problem.id == tc.problem_id).first()
    if not problem or not problem.reference_solution:
        return {"verified": False, "error": "No reference solution available"}
    executor = get_execution_service()
    result = await executor.execute(
        code=problem.reference_solution,
        language="python",
        test_cases=[{"input": tc.input_data, "output": tc.expected_output}],
    )
    actual_output = ""
    if result.get("test_results"):
        actual_output = result["test_results"][0].get("actual_output", "")
    return {
        "verified": result["status"] == "accepted",
        "actual_output": actual_output,
        "error": result.get("error_message"),
    }
