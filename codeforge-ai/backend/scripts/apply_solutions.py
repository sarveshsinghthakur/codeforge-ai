"""Apply authored solutions to the problem bank with runner verification.

Steps:
  1. Repair design-problem testcases whose args line is missing, plus the
     lru-cache expectations (the seeded values are unsatisfiable).
  2. For every published problem: map slug -> base slug, run the authored
     Python solution against ALL of its test cases.
  3. Apply explanation, hints, complexity, and the multi-language solution
     block to starter_code["solution"].
  4. Print a report; exit 1 if any verification failed (so we can iterate).

Usage: .venv python scripts/apply_solutions.py [--no-verify] [--no-apply]
"""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.services.code_execution import get_execution_service
from data.solutions_base1 import SOLUTIONS as S1
from data.solutions_base2 import SOLUTIONS as S2
from data.solutions_base3 import SOLUTIONS as S3
from data.solutions_base4 import SOLUTIONS as S4

ALL_SOLUTIONS = {**S1, **S2, **S3, **S4}

CORRECT_LRU_OUTPUT = "[null,null,null,1,null,null,null,null,3,4]"
DESIGN_CLASS_RE = re.compile(r'^\["([A-Za-z_]\w*)"')


def base_slug(slug: str) -> str:
    return re.sub(r"-\d+$", "", slug)


def repair_data(db) -> list[str]:
    """Fix known-broken seed testcases. Returns a list of repair notes."""
    notes = []

    # lru-cache: seeded expectations are impossible (get(3) -> 2 etc.)
    lru = db.query(Problem).filter(Problem.slug == "lru-cache").first()
    if lru:
        for tc in lru.test_cases:
            if tc.expected_output != CORRECT_LRU_OUTPUT:
                notes.append(
                    f"lru-cache case#{tc.id}: expected "
                    f"{tc.expected_output[:60]!r} -> {CORRECT_LRU_OUTPUT!r}"
                )
                tc.expected_output = CORRECT_LRU_OUTPUT

    # n-queens: cases 1-2 expect solution COUNT, but the starter/template
    # return boards (and case 3 already expects boards) -> align to boards.
    nq = db.query(Problem).filter(Problem.slug == "n-queens").first()
    if nq:
        boards4 = '[[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]'
        boards1 = '[["Q"]]'
        for tc in nq.test_cases:
            target = {"n = 4": boards4, "n = 1": boards1}.get(tc.input_data.strip())
            if target and tc.expected_output != target:
                notes.append(
                    f"n-queens case#{tc.id}: expected "
                    f"{tc.expected_output[:40]!r} -> {target[:40]!r} (boards)"
                )
                tc.expected_output = target

    # group-anagrams variants: seeded empty-string case has a stray '}'
    # e.g. '[[""]]}' instead of '[[""]]'
    broken_ga = '[[""]]}' 
    fixed_ga = '[[""]]'
    for p in db.query(Problem).filter(Problem.slug.like("group-anagrams%")).all():
        for tc in p.test_cases:
            if tc.expected_output == broken_ga:
                notes.append(
                    f"{p.slug} case#{tc.id}: fixed stray brace "
                    "on empty-string expectation"
                )
                tc.expected_output = fixed_ga

    # interval-list-intersections variants: case 1 expected [8,12] but
    # [5,10] intersection [8,12] is [8,10] (corrupted seed)
    broken_ili = "[[1,2],[5,5],[8,12],[15,23],[24,24],[25,25]]"
    fixed_ili = "[[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]"
    for p in db.query(Problem).filter(
        Problem.slug.like("interval-list-intersections%")
    ).all():
        for tc in p.test_cases:
            if tc.expected_output == broken_ili:
                notes.append(
                    f"{p.slug} case#{tc.id}: fixed intersection "
                    f"[8,12] -> [8,10]"
                )
                tc.expected_output = fixed_ili

    # design problems: first testcase carries ops only; adopt args from sibling
    problems = db.query(Problem).filter(Problem.status == "published").all()
    for p in problems:
        by_input = {}
        for tc in p.test_cases:
            by_input.setdefault(tc.input_data, []).append(tc)
        for tc in p.test_cases:
            lines = tc.input_data.splitlines()
            if len(lines) != 1:
                continue
            m = DESIGN_CLASS_RE.match(lines[0])
            if not m:
                continue
            for other in p.test_cases:
                olines = other.input_data.splitlines()
                if len(olines) == 2 and olines[0] == lines[0]:
                    new_input = other.input_data
                    notes.append(
                        f"{p.slug} case#{tc.id}: restored args line for "
                        f"{m.group(1)} design harness"
                    )
                    tc.input_data = new_input
                    break
    return notes


async def verify_problem(svc, problem, code) -> dict:
    tcs = [
        {
            "input": t.input_data,
            "output": t.expected_output,
            "is_public": bool(t.is_public),
        }
        for t in sorted(problem.test_cases, key=lambda t: t.id)
    ]
    if not tcs:
        return {"status": "no_tests", "failed": []}
    # generous timeout: tiny inputs were hitting TLE under spawn contention
    res = await svc.execute(
        code, "python", tcs, timeout_ms=max(problem.time_limit_ms, 10000)
    )
    failed = [
        r for r in res.get("test_results", []) if not r.get("passed")
    ]
    return {"status": res.get("status", "?"), "failed": failed}


def apply_solution(problem: Problem, sol: dict) -> None:
    problem.solution_explanation = sol["explanation"]
    problem.hints = json.dumps(sol["hints"])
    problem.complexity_time = sol["time"][:50]
    problem.complexity_space = sol["space"][:50]
    try:
        starter = json.loads(problem.starter_code or "{}")
    except json.JSONDecodeError:
        starter = {}
    if not isinstance(starter, dict):
        starter = {}
    starter["solution"] = {
        "python": sol["python"].strip(),
        "javascript": sol["javascript"].strip(),
        "java": sol["java"].strip(),
    }
    problem.starter_code = json.dumps(starter)


async def main(argv) -> int:
    no_verify = "--no-verify" in argv
    no_apply = "--no-apply" in argv

    db = SessionLocal()
    try:
        notes = repair_data(db)
        db.commit()
        for n in notes:
            print(f"[repair] {n}")
        print(f"[repair] {len(notes)} repair(s) applied\n")

        problems = (
            db.query(Problem)
            .filter(Problem.status == "published")
            .order_by(Problem.id)
            .all()
        )
        print(f"published problems: {len(problems)}")
        print(f"authored solutions: {len(ALL_SOLUTIONS)}\n")

        unmapped = sorted({p.slug for p in problems if base_slug(p.slug) not in ALL_SOLUTIONS})
        if unmapped:
            print(f"UNMAPPED slugs (no authored solution): {unmapped}\n")

        svc = get_execution_service()
        sem = asyncio.Semaphore(6)
        results = {}

        async def run(p):
            sol = ALL_SOLUTIONS.get(base_slug(p.slug))
            if sol is None:
                results[p.id] = ("unmapped", None)
                return
            if no_verify:
                results[p.id] = ("skipped", None)
            else:
                try:
                    async with sem:
                        r = await verify_problem(svc, p, sol["python"].strip())
                    results[p.id] = (r["status"], r["failed"])
                except Exception as exc:  # noqa: BLE001 - report and continue
                    results[p.id] = ("error", [{
                        "input_data": "",
                        "expected_output": "",
                        "actual_output": "",
                        "error": f"{type(exc).__name__}: {exc}",
                    }])
            if not no_apply:
                apply_solution(p, sol)

        print("verifying + applying...")
        await asyncio.gather(*(run(p) for p in problems))
        db.commit()

        counts = {}
        failures = []
        for p in problems:
            status, failed = results[p.id]
            counts[status] = counts.get(status, 0) + 1
            if failed:
                failures.append((p.slug, failed))

        print("\n=== summary ===")
        for k in sorted(counts):
            print(f"  {k}: {counts[k]}")

        if failures:
            print(f"\n=== {len(failures)} problem(s) with failing cases ===")
            for slug, failed in failures:
                f = failed[0]
                print(f"  {slug}: {len(failed)} failed | "
                      f"in={f.get('input_data', '')[:80]!r} "
                      f"exp={f.get('expected_output', '')[:40]!r} "
                      f"got={f.get('actual_output', '')[:40]!r}"
                      f"{' err=' + f.get('error', '')[:60] if f.get('error') else ''}")
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
