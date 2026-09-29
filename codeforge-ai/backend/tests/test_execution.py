"""Unit tests for the isolated code execution engine."""
import asyncio
import pytest

from app.services.code_execution import CodeExecutionService, get_execution_service


@pytest.fixture(scope="module")
def svc() -> CodeExecutionService:
    return get_execution_service()


def run(svc, code, test_cases, language="python", timeout_ms=4000):
    return asyncio.run(
        svc.execute(code=code, language=language, test_cases=test_cases, timeout_ms=timeout_ms)
    )


# ── input parsing ─────────────────────────────────────────────────────────

def test_parse_multi_assignment_one_line(svc):
    args, kwargs = svc.parse_input("nums = [2,7,11,15], target = 9")
    assert args == []
    assert kwargs == {"nums": [2, 7, 11, 15], "target": 9}


def test_parse_multiline_assignments(svc):
    args, kwargs = svc.parse_input("numCourses = 2\nprerequisites = [[1,0]]")
    assert kwargs == {"numCourses": 2, "prerequisites": [[1, 0]]}


def test_parse_bare_literal(svc):
    args, kwargs = svc.parse_input("[1,2,3]")
    assert args == [[1, 2, 3]] and kwargs == {}


def test_parse_bare_string(svc):
    args, kwargs = svc.parse_input("abcabcbb")
    assert args == ["abcabcbb"]


def test_parse_int(svc):
    args, kwargs = svc.parse_input("121")
    assert args == [121]


def test_parse_json_null(svc):
    _, kwargs = svc.parse_input("root = [3,9,20,null,null,15,7]")
    assert kwargs["root"][3] is None


def test_parse_string_with_equals(svc):
    _, kwargs = svc.parse_input('s = "a=b"')
    assert kwargs["s"] == "a=b"


# ── execution outcomes ────────────────────────────────────────────────────

TWO_SUM_OK = """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
"""

TWO_SUM_WRONG = """
class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
"""

TWO_SUM_CASES = [
    {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "is_public": True},
    {"input": "nums = [3,2,4], target = 6", "output": "[1,2]", "is_public": True},
    {"input": "nums = [3,3], target = 6", "output": "[0,1]", "is_public": False},
]


def test_accepted(svc):
    result = run(svc, TWO_SUM_OK, TWO_SUM_CASES)
    assert result["status"] == "accepted", result
    assert result["total_passed"] == 3
    assert result["runtime_ms"] >= 0


def test_wrong_answer(svc):
    result = run(svc, TWO_SUM_WRONG, TWO_SUM_CASES)
    assert result["status"] == "wrong_answer"
    # case 1 ([0,1]) and case 3 ([3,3] -> [0,1]) coincidentally match
    assert result["total_passed"] == 2
    failed = [r for r in result["test_results"] if not r["passed"]][0]
    assert failed["expected_output"] == "[1,2]"
    assert failed["actual_output"] == "[0,1]"


def test_compilation_error(svc):
    result = run(svc, "class Solution:\n    def twoSum(self, a):\n   bad indent", TWO_SUM_CASES[:1])
    assert result["status"] == "compilation_error"
    assert "SyntaxError" in (result["error_message"] or "")


def test_runtime_error(svc):
    code = "class Solution:\n    def twoSum(self, nums, target):\n        raise ValueError('boom')"
    result = run(svc, code, TWO_SUM_CASES[:1])
    assert result["status"] == "runtime_error"
    assert "boom" in (result["error_message"] or "")


def test_time_limit(svc):
    code = "class Solution:\n    def twoSum(self, nums, target):\n        while True:\n            pass"
    result = run(svc, code, TWO_SUM_CASES[:1], timeout_ms=1500)
    assert result["status"] == "time_limit"


def test_linked_list_with_cycle(svc):
    code = """
class ListNode:
    def __init__(self, x=0):
        self.val = x
        self.next = None
class Solution:
    def hasCycle(self, head):
        seen = set()
        while head:
            if id(head) in seen:
                return True
            seen.add(id(head))
            head = head.next
        return False
"""
    cases = [
        {"input": "head = [3,2,0,-4], pos = 1", "output": "true", "is_public": True},
        {"input": "head = [1], pos = -1", "output": "false", "is_public": True},
    ]
    result = run(svc, code, cases)
    assert result["status"] == "accepted", result


def test_binary_tree(svc):
    code = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def maxDepth(self, root) -> int:
        if root is None:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
"""
    cases = [
        {"input": "root = [3,9,20,null,null,15,7]", "output": "3", "is_public": True},
        {"input": "root = [1,null,2]", "output": "2", "is_public": True},
        {"input": "root = []", "output": "0", "is_public": True},
    ]
    result = run(svc, code, cases)
    assert result["status"] == "accepted", result


def test_order_insensitive_nested_lists(svc):
    code = """
class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for s in strs:
            groups.setdefault(''.join(sorted(s)), []).append(s)
        return list(groups.values())
"""
    cases = [{"input": 'strs = ["eat","tea","tan"]', "output": '[["eat","tea"],["tan"]]', "is_public": True}]
    result = run(svc, code, cases)
    assert result["status"] == "accepted", result


def test_javascript_execution(svc):
    if not any(l["id"] == "javascript" and l["available"] for l in svc.available_languages()):
        pytest.skip("node not available")
    code = "var twoSum = function(nums, target) {\n  const seen = new Map();\n  for (let i = 0; i < nums.length; i++) {\n    const c = target - nums[i];\n    if (seen.has(c)) return [seen.get(c), i];\n    seen.set(nums[i], i);\n  }\n  return [];\n};"
    result = run(svc, code, TWO_SUM_CASES, language="javascript")
    assert result["status"] == "accepted", result


def test_hidden_results_flagged(svc):
    result = run(svc, TWO_SUM_OK, TWO_SUM_CASES)
    flags = [r["is_public"] for r in result["test_results"]]
    assert flags == [True, True, False]


def test_unsupported_language(svc):
    result = asyncio.run(svc.execute(code="int main(){}", language="cpp", test_cases=[]))
    assert result["status"] == "compilation_error"
