"""Seed 100 coding problems with test cases into SQLite."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.core.security import get_password_hash

def extract_test_cases_from_description(description: str) -> list:
    """Extract test cases from the description area."""
    test_cases = []
    
    # Check if description has additional test cases section
    if "Additional Test Cases:" in description:
        # Split the description
        parts = description.split("Additional Test Cases:")
        desc_part = parts[0].strip()
        
        # Extract test cases from the additional section
        additional_section = parts[1].strip()
        
        # Look for patterns like "Input: ...\nOutput: ..."
        test_case_pattern = r'Input:\s*([^\n]+)\s*Output:\s*([^\n]+)'
        matches = re.findall(test_case_pattern, additional_section, re.MULTILINE)
        
        for match in matches:
            test_cases.append({
                "input": match[0].strip(),
                "output": match[1].strip()
            })
    
    return test_cases

def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create admin user
    admin = User(
        username="admin",
        email="admin@codeforge.ai",
        hashed_password=get_password_hash("admin123"),
        display_name="Admin",
        role="ADMIN",
        is_active=True,
    )
    db.add(admin)
    db.commit()

    # Load problems from JSON file
    json_path = os.path.join(os.path.dirname(__file__), "problems.json")
    with open(json_path, "r", encoding="utf-8") as f:
        problems = json.load(f)

    for i, p in enumerate(problems):
        # Extract test cases from description
        description_test_cases = extract_test_cases_from_description(p.get("description", ""))
        
        # Set difficulty for generated problems
        difficulty = p.get("difficulty", "unknown")
        
        problem = Problem(
            title=p["title"],
            slug=p["slug"],
            difficulty=difficulty,
            description=p["description"],
            topics=json.dumps(p.get("topics", [])),
            constraints=json.dumps(p.get("constraints", [])),
            examples=json.dumps(p.get("examples", [])),
            hints=json.dumps(p.get("hints", [])),
            starter_code=json.dumps(p.get("starter_code", {})),
            complexity_time=p.get("complexity_time"),
            complexity_space=p.get("complexity_space"),
            status="published",
            acceptance_rate=0.0,
            solved_count=0,
            attempt_count=0,
            time_limit_ms=2000,
            memory_limit_mb=256,
            created_by=admin.id,
        )
        db.add(problem)
        db.flush()

        # Add test cases from examples (up to 3 public test cases)
        examples = p.get("examples", [])
        for j, ex in enumerate(examples[:3]):
            tc = TestCase(
                problem_id=problem.id,
                input_data=ex.get("input", ""),
                expected_output=ex.get("output", ""),
                is_public=True,
                order_index=j,
            )
            db.add(tc)

        # Also add the dedicated test_input/test_output as a hidden test case
        test_input = p.get("test_input", "")
        test_output = p.get("test_output", "")
        if test_input and test_input != (examples[0].get("input", "") if examples else ""):
            tc = TestCase(
                problem_id=problem.id,
                input_data=test_input,
                expected_output=test_output,
                is_public=False,
                is_edge_case=True,
                order_index=len(examples[:3]),
            )
            db.add(tc)
        
        # Add additional test cases from description as hidden test cases
        for j, ex in enumerate(description_test_cases):
            tc = TestCase(
                problem_id=problem.id,
                input_data=ex.get("input", ""),
                expected_output=ex.get("output", ""),
                is_public=False,
                is_edge_case=True,
                order_index=len(examples[:3]) + len(description_test_cases[:j]),
            )
            db.add(tc)

        if (i + 1) % 20 == 0:
            db.commit()
            print(f"  Seeded {i + 1}/{len(problems)} problems...")

    db.commit()
    db.close()
    print(f"Done! Seeded {len(problems)} problems.")
    print(f"Total test cases added: {sum(len(extract_test_cases_from_description(p.get('description', ''))) for p in problems)}")


if __name__ == "__main__":
    seed()