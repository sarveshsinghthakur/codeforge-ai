"""Problem quality checker."""
from typing import List, Dict, Any, Optional


class ProblemQualityChecker:
    """Validates AI-generated problems before publishing."""

    def check(
        self,
        data: dict,
        reference_solution: str = None,
        test_cases: List[dict] = None,
    ) -> dict:
        """Run quality checks. Returns report."""
        errors: List[str] = []
        warnings: List[str] = []

        # Statement completeness
        if not data.get("title") or len(data["title"]) < 3:
            errors.append("Title is too short or missing")
        if not data.get("description") or len(data["description"]) < 50:
            errors.append("Description is too short (minimum 50 characters)")
        if not data.get("topics") or len(data["topics"]) == 0:
            warnings.append("No topics assigned")

        # Constraints consistency
        if not data.get("constraints") or len(data["constraints"]) < 2:
            warnings.append("Fewer than 2 constraints")
        for c in data.get("constraints", []):
            if len(c) < 5:
                warnings.append(f"Constraint too short: '{c[:50]}...'")

        # Examples
        examples = data.get("examples", [])
        if len(examples) < 2:
            errors.append("At least 2 examples required")
        for i, ex in enumerate(examples):
            if "input" not in ex:
                errors.append(f"Example {i+1} missing 'input'")
            if "output" not in ex:
                errors.append(f"Example {i+1} missing 'output'")
            if "explanation" not in ex:
                warnings.append(f"Example {i+1} missing 'explanation'")

        # Starter code
        starter = data.get("starter_code", {})
        required = ["python", "javascript", "java", "cpp", "c"]
        for lang in required:
            if lang not in starter:
                errors.append(f"Missing starter code for {lang}")
            elif not starter[lang] or len(starter[lang]) < 5:
                errors.append(f"Empty starter code for {lang}")

        # Reference solution
        if not reference_solution:
            warnings.append("No reference solution — test verification limited")
        else:
            try:
                compile(reference_solution, "<test>", "exec")
            except SyntaxError as e:
                errors.append(f"Reference solution syntax error: {e}")

        # Test cases
        if not test_cases or len(test_cases) < 3:
            errors.append("At least 3 test cases required")
        for i, tc in enumerate(test_cases or []):
            if "input" not in tc or not tc["input"]:
                errors.append(f"Test case {i+1} missing input")
            if "output" not in tc or tc["output"] is None:
                warnings.append(f"Test case {i+1} missing expected output")

        # Duplicate detection
        seen = set()
        dups = 0
        for tc in test_cases or []:
            key = (tc.get("input", ""), tc.get("output", ""))
            if key in seen:
                dups += 1
            seen.add(key)
        if dups > 0:
            warnings.append(f"{dups} duplicate test case(s) detected")

        # Complexity
        complexity = data.get("complexity", {})
        if not complexity.get("time"):
            warnings.append("Time complexity not specified")

        # Wording
        description = data.get("description", "")
        if "TODO" in description or "FIXME" in description:
            errors.append("Description contains TODO/FIXME placeholders")

        # Difficulty
        if data.get("difficulty") not in ("easy", "medium", "hard"):
            errors.append("Invalid difficulty level")

        return {
            "statement": "PASS" if not any("title" in e.lower() or "description" in e.lower() or "topics" in e.lower() for e in errors) else "FAIL",
            "examples": "PASS" if not any("example" in e.lower() for e in errors) else "FAIL",
            "constraints": "PASS" if not any("constraint" in e.lower() for e in errors) else ("WARNING" if warnings else "PASS"),
            "starter_code": "PASS" if not any("starter" in e.lower() for e in errors) else "FAIL",
            "reference_solution": "PASS" if not any("reference" in e.lower() for e in errors) else "FAIL",
            "test_cases": "PASS" if not any("test case" in e.lower() for e in errors) else "FAIL",
            "complexity": "PASS" if not any("complexity" in e.lower() for e in errors) else "WARNING",
            "overall": "PASS" if len(errors) == 0 else "FAIL",
            "warnings": warnings,
            "errors": errors,
        }


quality_checker = ProblemQualityChecker()


def get_quality_checker() -> ProblemQualityChecker:
    return quality_checker
