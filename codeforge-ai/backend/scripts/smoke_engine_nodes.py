"""Engine smoke: node returns, design harness, serialize, regression.

Run: .venv python scripts/smoke_engine_nodes.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.code_execution import get_execution_service

PY = "python"
JS = "javascript"

CASES = [
    (
        "lca-value-python",
        PY,
        """
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution:
    def lowestCommonAncestor(self, root, p, q):
        tp = p.val if hasattr(p, 'val') else p
        tq = q.val if hasattr(q, 'val') else q
        if not root:
            return None
        if root.val == tp or root.val == tq:
            return root
        left = self.lowestCommonAncestor(root.left, tp, tq)
        right = self.lowestCommonAncestor(root.right, tp, tq)
        if left and right:
            return root
        return left or right
""",
        [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1", "output": "3", "is_public": True}],
    ),
    (
        "serialize-python",
        PY,
        """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    def serialize(self, root):
        if root is None:
            return '[]'
        out = []
        queue = [root]
        while queue:
            node = queue.pop(0)
            if node is None:
                out.append('null')
                continue
            out.append(str(node.val))
            queue.append(node.left)
            queue.append(node.right)
        while out and out[-1] == 'null':
            out.pop()
        return '[' + ','.join(out) + ']'

def serialize(root):
    return Codec().serialize(root)
""",
        [
            {"input": "root = [1,2,3,null,null,4,5]", "output": "[1,2,3,null,null,4,5]", "is_public": True},
            {"input": "root = []", "output": "[]", "is_public": True},
            {"input": "[1,2,3,null,null,4,5]", "output": "[1,2,3,null,null,4,5]", "is_public": True},
        ],
    ),
    (
        "lru-design-python",
        PY,
        """
class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.data = {}
        self.order = []

    def get(self, key):
        if key not in self.data:
            return None
        self.order.remove(key)
        self.order.append(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            self.order.remove(key)
            self.order.append(key)
            return
        self.data[key] = value
        self.order.append(key)
        if len(self.order) > self.cap:
            old = self.order.pop(0)
            del self.data[old]
""",
        [
            {
                "input": '["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]',
                "output": "[null,null,null,1,null,null,null,null,3,4]",
                "is_public": True,
            },
            {
                "input": '["LRUCache","put","get"]\n[[1],[1,7],[1]]',
                "output": "[null,null,7]",
                "is_public": True,
            },
        ],
    ),
    (
        "median-design-python",
        PY,
        """
class MedianFinder:
    def __init__(self):
        self.nums = []

    def addNum(self, num):
        self.nums.append(num)
        self.nums.sort()

    def findMedian(self):
        n = len(self.nums)
        mid = n // 2
        if n % 2:
            return float(self.nums[mid])
        return (self.nums[mid - 1] + self.nums[mid]) / 2.0
""",
        [
            {
                "input": '["MedianFinder","addNum","addNum","findMedian","addNum","findMedian"]\n[[],[1],[2],[],[3],[]]',
                "output": "[null,null,null,1.5,null,2.0]",
                "is_public": True,
            },
        ],
    ),
    (
        "two-sum-regression",
        PY,
        """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            comp = target - n
            if comp in seen:
                return [seen[comp], i]
            seen[n] = i
        return []
""",
        [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "is_public": True}],
    ),
    (
        "lca-js",
        JS,
        """
var lowestCommonAncestor = function(root, p, q) {
    const tp = (p && typeof p === 'object') ? p.val : p;
    const tq = (q && typeof q === 'object') ? q.val : q;
    if (!root) return null;
    if (root.val === tp || root.val === tq) return root;
    const left = lowestCommonAncestor(root.left, tp, tq);
    const right = lowestCommonAncestor(root.right, tp, tq);
    if (left && right) return root;
    return left || right;
};
""",
        [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4", "output": "5", "is_public": True}],
    ),
    (
        "lru-design-js",
        JS,
        """
var LRUCache = function(capacity) {
    this.cap = capacity;
    this.map = new Map();
};
LRUCache.prototype.get = function(key) {
    if (!this.map.has(key)) return null;
    const v = this.map.get(key);
    this.map.delete(key);
    this.map.set(key, v);
    return v;
};
LRUCache.prototype.put = function(key, value) {
    if (this.map.has(key)) this.map.delete(key);
    this.map.set(key, value);
    if (this.map.size > this.cap) {
        this.map.delete(this.map.keys().next().value);
    }
};
""",
        [
            {
                "input": '["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]',
                "output": "[null,null,null,1,null,null,null,null,3,4]",
                "is_public": True,
            },
        ],
    ),
    (
        "median-design-js",
        JS,
        """
var MedianFinder = function() {
    this.nums = [];
};
MedianFinder.prototype.addNum = function(num) {
    this.nums.push(num);
    this.nums.sort((a, b) => a - b);
};
MedianFinder.prototype.findMedian = function() {
    const n = this.nums.length;
    const mid = n >> 1;
    return n % 2 ? this.nums[mid] : (this.nums[mid - 1] + this.nums[mid]) / 2;
};
""",
        [
            {
                "input": '["MedianFinder","addNum","addNum","findMedian","addNum","findMedian"]\n[[],[1],[2],[],[3],[]]',
                "output": "[null,null,null,1.5,null,2.0]",
                "is_public": True,
            },
        ],
    ),
]


async def main():
    svc = get_execution_service()
    failures = []
    for name, lang, code, tcs in CASES:
        res = await svc.execute(code, lang, tcs, timeout_ms=8000)
        status = res["status"]
        detail = [
            (r["passed"], r["expected_output"], r["actual_output"], r["error"])
            for r in res["test_results"]
        ]
        mark = "PASS" if status == "accepted" else "FAIL"
        print(f"[{mark}] {name}: {status} {detail}")
        if status != "accepted":
            failures.append(name)
    print(f"\n{len(CASES) - len(failures)}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
