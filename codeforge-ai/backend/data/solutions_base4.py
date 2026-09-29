"""Real solutions + explanations for base problems (batch 4/4): russian-doll-envelopes .. word-search."""

SOLUTIONS = {
    "russian-doll-envelopes": {
        "time": "O(n log n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Sort envelopes by width ascending; on equal width sort by height **descending** - this lets every inner doll of the same width pass through the LIS filter without forming an invalid pair.
2. After sorting, the problem reduces to the Longest Increasing Subsequence on the height array.
3. Compute the LIS of heights with a patience-sorting `tails` array in `O(n log n)`.

The width constraint is neutralized by the sort, leaving only the height ordering to solve.""",
        "hints": [
            "Sort by width ASC, but height DESC for ties - otherwise equal widths form a false chain.",
            "Once sorted, only the heights matter: run the classic LIS on them.",
            "Use the O(n log n) tails/binary-search LIS, not the O(n^2) DP, to stay within limits.",
        ],
        "python": """
import bisect

class Solution:
    def maxEnvelopes(self, envelopes):
        envelopes.sort(key=lambda e: (e[0], -e[1]))
        tails = []
        for _, h in envelopes:
            i = bisect.bisect_left(tails, h)
            if i == len(tails):
                tails.append(h)
            else:
                tails[i] = h
        return len(tails)
""",
        "javascript": """
var maxEnvelopes = function(envelopes) {
    envelopes.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
    const tails = [];
    for (const [, h] of envelopes) {
        let lo = 0, hi = tails.length;
        while (lo < hi) {
            const mid = (lo + hi) >> 1;
            if (tails[mid] < h) lo = mid + 1;
            else hi = mid;
        }
        if (lo === tails.length) tails.push(h);
        else tails[lo] = h;
    }
    return tails.length;
};
""",
        "java": """
class Solution {
    public int maxEnvelopes(int[][] envelopes) {
        Arrays.sort(envelopes, (a, b) -> a[0] != b[0] ? a[0] - b[0] : b[1] - a[1]);
        int[] tails = new int[envelopes.length];
        int size = 0;
        for (int[] e : envelopes) {
            int lo = 0, hi = size;
            while (lo < hi) {
                int mid = lo + (hi - lo) / 2;
                if (tails[mid] < e[1]) lo = mid + 1;
                else hi = mid;
            }
            tails[lo] = e[1];
            if (lo == size) size++;
        }
        return size;
    }
}
""",
    },
    "search-in-rotated-sorted-array": {
        "time": "O(log n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Binary search on `[lo, hi]`; at least one half is always sorted.
2. If the **left half** (`nums[lo] <= nums[mid]`) is sorted:
   - If `target` lies inside `[nums[lo], nums[mid])`, search left; otherwise search right.
3. Else the right half is sorted:
   - If `target` lies inside `(nums[mid], nums[hi]]`, search right; otherwise search left.
4. Each step discards half the range while correctly accounting for the rotation.

`O(log n)` even though the array is rotated.""",
        "hints": [
            "Check which side is sorted before deciding where target can live.",
            "Use <= when testing the left half and > when testing the right so boundaries are exclusive-correct.",
            "All elements are distinct here, so the pivot never confuses equal values.",
        ],
        "python": """
class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[lo] <= nums[mid]:
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        return -1
""",
        "javascript": """
var search = function(nums, target) {
    let lo = 0, hi = nums.length - 1;
    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (nums[mid] === target) return mid;
        if (nums[lo] <= nums[mid]) {
            if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
            else lo = mid + 1;
        } else {
            if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;
};
""",
        "java": """
class Solution {
    public int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }
}
""",
    },
    "search-insert-position": {
        "time": "O(log n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Binary search for the leftmost index where `nums[i] >= target` (lower bound).
2. If `target` is found, that index is the answer; if not, the lower-bound position is exactly where `target` would be inserted to keep the array sorted.
3. Standard invariant: `lo` is always a valid insertion candidate; `hi` converges to the answer.

`O(log n)` time, `O(1)` space.""",
        "hints": [
            "You want the FIRST position with value >= target, not just any match.",
            "Loop while lo < hi with mid = (lo + hi) // 2, shrinking to lo = mid + 1 or hi = mid.",
            "When the loop ends, lo is the insertion index whether target exists or not.",
        ],
        "python": """
class Solution:
    def searchInsert(self, nums, target):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo
""",
        "javascript": """
var searchInsert = function(nums, target) {
    let lo = 0, hi = nums.length;
    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (nums[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
};
""",
        "java": """
class Solution {
    public int searchInsert(int[] nums, int target) {
        int lo = 0, hi = nums.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }
}
""",
    },
    "serialize-and-deserialize-binary-tree": {
        "time": "O(n) both ways",
        "space": "O(n)",
        "explanation": """**Approach**

1. `serialize` does a breadth-first walk, emitting each node's value and the literal `null` for every missing child slot - exactly the LeetCode level-order array format.
2. Trailing `null`s are trimmed (they carry no structural information), so `[1,2,null,null,3]` becomes `[1,2,3]`.
3. `deserialize` rebuilds the tree from that array: the first value is the root, then each dequeued node consumes the next two entries as its left and right child.
4. `null` entries occupy a child slot but enqueue nothing - their children do not exist.

Both passes touch every node exactly once.""",
        "hints": [
            "BFS with a queue: append children only for real nodes, emit 'null' for empty slots.",
            "Trim trailing nulls - they add nothing to the encoding.",
            "Deserialize by consuming two array entries per dequeued node.",
        ],
        "python": """
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

    def deserialize(self, data):
        if data in ('[]', '', 'null'):
            return None
        tokens = data.strip('[]').split(',')
        root = TreeNode(int(tokens[0]))
        queue = [root]
        i = 1
        while queue and i < len(tokens):
            node = queue.pop(0)
            if tokens[i] != 'null':
                node.left = TreeNode(int(tokens[i]))
                queue.append(node.left)
            i += 1
            if i < len(tokens):
                if tokens[i] != 'null':
                    node.right = TreeNode(int(tokens[i]))
                    queue.append(node.right)
                i += 1
        return root


def serialize(root):
    return Codec().serialize(root)


def deserialize(data):
    return Codec().deserialize(data)
""",
        "javascript": """
var serialize = function(root) {
    if (!root) return '[]';
    const out = [];
    let queue = [root];
    while (queue.length) {
        const node = queue.shift();
        if (node === null) { out.push('null'); continue; }
        out.push(String(node.val));
        queue.push(node.left);
        queue.push(node.right);
    }
    while (out.length && out[out.length - 1] === 'null') out.pop();
    return '[' + out.join(',') + ']';
};

var deserialize = function(data) {
    if (!data || data === '[]' || data === 'null') return null;
    const tokens = data.slice(1, -1).split(',');
    const root = new TreeNode(parseInt(tokens[0], 10));
    const queue = [root];
    let i = 1;
    while (queue.length && i < tokens.length) {
        const node = queue.shift();
        if (tokens[i] !== 'null') {
            node.left = new TreeNode(parseInt(tokens[i], 10));
            queue.push(node.left);
        }
        i++;
        if (i < tokens.length) {
            if (tokens[i] !== 'null') {
                node.right = new TreeNode(parseInt(tokens[i], 10));
                queue.push(node.right);
            }
            i++;
        }
    }
    return root;
};
""",
        "java": """
public class Codec {
    public String serialize(TreeNode root) {
        if (root == null) return "[]";
        List<String> out = new ArrayList<>();
        Queue<TreeNode> queue = new LinkedList<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            if (node == null) { out.add("null"); continue; }
            out.add(String.valueOf(node.val));
            queue.add(node.left);
            queue.add(node.right);
        }
        int end = out.size() - 1;
        while (end >= 0 && out.get(end).equals("null")) end--;
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i <= end; i++) {
            if (i > 0) sb.append(',');
            sb.append(out.get(i));
        }
        return sb.append(']').toString();
    }

    public TreeNode deserialize(String data) {
        if (data.equals("[]") || data.isEmpty() || data.equals("null")) return null;
        String[] tokens = data.substring(1, data.length() - 1).split(",");
        TreeNode root = new TreeNode(Integer.parseInt(tokens[0]));
        Queue<TreeNode> queue = new LinkedList<>();
        queue.add(root);
        int i = 1;
        while (!queue.isEmpty() && i < tokens.length) {
            TreeNode node = queue.poll();
            if (!tokens[i].equals("null")) {
                node.left = new TreeNode(Integer.parseInt(tokens[i]));
                queue.add(node.left);
            }
            i++;
            if (i < tokens.length) {
                if (!tokens[i].equals("null")) {
                    node.right = new TreeNode(Integer.parseInt(tokens[i]));
                    queue.add(node.right);
                }
                i++;
            }
        }
        return root;
    }
}
""",
    },
    "single-number": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Every element appears twice except one. XOR has the properties `x ^ x = 0` and `0 ^ x = x`.
2. XOR the whole array: all pairs cancel and only the unique element survives.

One pass, constant memory, no sorting.""",
        "hints": [
            "XOR pairs cancel out - the duplicate vanishes automatically.",
            "Initialize the accumulator to 0 (identity for XOR).",
            "Sorting or a hash set also works, but breaks the O(1) space requirement.",
        ],
        "python": """
class Solution:
    def singleNumber(self, nums):
        xor = 0
        for n in nums:
            xor ^= n
        return xor
""",
        "javascript": """
var singleNumber = function(nums) {
    let xor = 0;
    for (const n of nums) xor ^= n;
    return xor;
};
""",
        "java": """
class Solution {
    public int singleNumber(int[] nums) {
        int xor = 0;
        for (int n : nums) xor ^= n;
        return xor;
    }
}
""",
    },
    "sliding-window-maximum": {
        "time": "O(n)",
        "space": "O(k)",
        "explanation": """**Approach**

1. Keep a deque of indices whose values are **monotonically decreasing** - the front always holds the current window's maximum.
2. When adding index `i`, pop from the back while `nums[back] <= nums[i]` (those values are both smaller and older, so useless).
3. Pop the front if it has slid out of the window (`front <= i - k`).
4. From `i >= k - 1` record `nums[deque[0]]` as the window maximum.

Each index enters and leaves the deque at most once, so the whole scan is linear.""",
        "hints": [
            "Store INDICES in the deque so you can test eviction by position.",
            "Keep values decreasing from front to back; the front is always the max.",
            "Start recording answers only once the first full window is formed.",
        ],
        "python": """
from collections import deque

class Solution:
    def maxSlidingWindow(self, nums, k):
        dq = deque()
        res = []
        for i, n in enumerate(nums):
            while dq and nums[dq[-1]] <= n:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                res.append(nums[dq[0]])
        return res
""",
        "javascript": """
var maxSlidingWindow = function(nums, k) {
    const dq = [];
    const res = [];
    for (let i = 0; i < nums.length; i++) {
        while (dq.length && nums[dq[dq.length - 1]] <= nums[i]) dq.pop();
        dq.push(i);
        if (dq[0] <= i - k) dq.shift();
        if (i >= k - 1) res.push(nums[dq[0]]);
    }
    return res;
};
""",
        "java": """
class Solution {
    public int[] maxSlidingWindow(int[] nums, int k) {
        Deque<Integer> dq = new ArrayDeque<>();
        int[] res = new int[nums.length - k + 1];
        int r = 0;
        for (int i = 0; i < nums.length; i++) {
            while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) dq.pollLast();
            dq.addLast(i);
            if (dq.peekFirst() <= i - k) dq.pollFirst();
            if (i >= k - 1) res[r++] = nums[dq.peekFirst()];
        }
        return res;
    }
}
""",
    },
    "sort-colors": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Dutch national flag: three pointers - `lo` (next position for a 0), `mid` (current element), `hi` (next position for a 2).
2. When `nums[mid] == 0`, swap with `nums[lo]` and advance both `lo` and `mid`.
3. When `nums[mid] == 2`, swap with `nums[hi]` and decrement `hi` (do **not** advance `mid` - the swapped-in value is unexamined).
4. When `nums[mid] == 1`, just advance `mid`.

A single pass with at most `n` swaps sorts the array in place; return `nums` so the judge can compare it.""",
        "hints": [
            "Three-way partition: [0s | 1s | unexamined | 2s].",
            "After swapping a 2 into place, re-examine mid - you do not know what came in.",
            "mid stops when it passes hi: everything beyond hi is already 2.",
        ],
        "python": """
class Solution:
    def sortColors(self, nums):
        lo, mid, hi = 0, 0, len(nums) - 1
        while mid <= hi:
            if nums[mid] == 0:
                nums[lo], nums[mid] = nums[mid], nums[lo]
                lo += 1
                mid += 1
            elif nums[mid] == 2:
                nums[mid], nums[hi] = nums[hi], nums[mid]
                hi -= 1
            else:
                mid += 1
        return nums
""",
        "javascript": """
var sortColors = function(nums) {
    let lo = 0, mid = 0, hi = nums.length - 1;
    while (mid <= hi) {
        if (nums[mid] === 0) {
            [nums[lo], nums[mid]] = [nums[mid], nums[lo]];
            lo++; mid++;
        } else if (nums[mid] === 2) {
            [nums[mid], nums[hi]] = [nums[hi], nums[mid]];
            hi--;
        } else mid++;
    }
    return nums;
};
""",
        "java": """
class Solution {
    public int[] sortColors(int[] nums) {
        int lo = 0, mid = 0, hi = nums.length - 1;
        while (mid <= hi) {
            if (nums[mid] == 0) {
                int t = nums[lo]; nums[lo] = nums[mid]; nums[mid] = t;
                lo++; mid++;
            } else if (nums[mid] == 2) {
                int t = nums[mid]; nums[mid] = nums[hi]; nums[hi] = t;
                hi--;
            } else mid++;
        }
        return nums;
    }
}
""",
    },
    "sum-of-two-numbers": {
        "time": "O(1)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Addition of two integers is a single arithmetic operation.
2. Return `a + b` directly - there is no trick, traversal, or data structure involved.

Constant time and constant space; the constraint is simply to avoid naive approaches for larger inputs (not applicable here).""",
        "hints": [
            "The two operands are plain integers - just add them.",
            "No loops or recursion are needed.",
            "Remember Python's ints are unbounded, so overflow is not a concern.",
        ],
        "python": """
class Solution:
    def sumOfTwo(self, a, b):
        return a + b
""",
        "javascript": """
var sumOfTwo = function(a, b) {
    return a + b;
};
""",
        "java": """
class Solution {
    public int sumOfTwo(int a, int b) {
        return a + b;
    }
}
""",
    },
    "symmetric-tree": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. The tree is a mirror of itself iff every node's left subtree mirrors its right subtree.
2. Recurse with a **pair** of nodes `(a, b)`: they match when both are null, or both have equal values and `(a.left, b.right)` and `(a.right, b.left)` match.
3. Note the crossed comparison: one side's left is compared to the other side's right.

Each pair of nodes is visited once - linear time, recursion depth equal to tree height.""",
        "hints": [
            "Compare left child of one node against RIGHT child of the other.",
            "Both null => match; one null => not a mirror.",
            "This is a simultaneous two-tree traversal, not two independent checks.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def isSymmetric(self, root):
        if not root:
            return True

        def mirror(a, b):
            if not a and not b:
                return True
            if not a or not b:
                return False
            return (a.val == b.val
                    and mirror(a.left, b.right)
                    and mirror(a.right, b.left))

        return mirror(root.left, root.right)
""",
        "javascript": """
var isSymmetric = function(root) {
    if (!root) return true;
    const mirror = (a, b) => {
        if (!a && !b) return true;
        if (!a || !b) return false;
        return a.val === b.val && mirror(a.left, b.right) && mirror(a.right, b.left);
    };
    return mirror(root.left, root.right);
};
""",
        "java": """
class Solution {
    public boolean isSymmetric(TreeNode root) {
        if (root == null) return true;
        return mirror(root.left, root.right);
    }
    private boolean mirror(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        return a.val == b.val && mirror(a.left, b.right) && mirror(a.right, b.left);
    }
}
""",
    },
    "top-k-frequent-elements": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Count frequencies with a hash map in `O(n)`.
2. Bucket sort: create `buckets[c]` = list of values occurring exactly `c` times (index up to `n`, the theoretical maximum frequency).
3. Walk buckets from highest frequency down, collecting elements until `k` are gathered.

Counting plus bucket traversal is linear overall, beating the `O(n log k)` heap alternative.""",
        "hints": [
            "Frequency can be at most n, so n+1 buckets suffice.",
            "Iterate buckets from the end (highest count) downward.",
            "All elements within one bucket are equally valid - any order is accepted.",
        ],
        "python": """
class Solution:
    def topKFrequent(self, nums, k):
        freq = {}
        for n in nums:
            freq[n] = freq.get(n, 0) + 1
        buckets = [[] for _ in range(len(nums) + 1)]
        for n, c in freq.items():
            buckets[c].append(n)
        res = []
        for c in range(len(buckets) - 1, 0, -1):
            for n in buckets[c]:
                res.append(n)
                if len(res) == k:
                    return res
        return res
""",
        "javascript": """
var topKFrequent = function(nums, k) {
    const freq = new Map();
    for (const n of nums) freq.set(n, (freq.get(n) || 0) + 1);
    const buckets = Array.from({ length: nums.length + 1 }, () => []);
    for (const [n, c] of freq) buckets[c].push(n);
    const res = [];
    for (let c = buckets.length - 1; c > 0; c--) {
        for (const n of buckets[c]) {
            res.push(n);
            if (res.length === k) return res;
        }
    }
    return res;
};
""",
        "java": """
class Solution {
    public int[] topKFrequent(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        for (int n : nums) freq.put(n, freq.getOrDefault(n, 0) + 1);
        List<Integer>[] buckets = new List[nums.length + 1];
        for (int i = 0; i < buckets.length; i++) buckets[i] = new ArrayList<>();
        for (Map.Entry<Integer, Integer> e : freq.entrySet()) buckets[e.getValue()].add(e.getKey());
        int[] res = new int[k];
        int idx = 0;
        for (int c = buckets.length - 1; c > 0 && idx < k; c++) {
            for (int n : buckets[c]) {
                if (idx == k) break;
                res[idx++] = n;
            }
        }
        return res;
    }
}
""",
    },
    "trapping-rain-water": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Water above index `i` = `min(max_left, max_right) - height[i]` (it is capped by the shorter of the two walls).
2. Two pointers `lo`/`hi` with running `left_max`/`right_max`: the side with the smaller wall is currently the binding constraint, so it can be resolved immediately.
3. When `height[lo] <= height[hi]`, accumulate `max(0, left_max - height[lo])`, update `left_max`, and advance `lo` (and symmetrically for the right).

Each position is settled exactly once, giving a single linear pass.""",
        "hints": [
            "You only need the MAX wall seen so far on each side.",
            "Process the side with the shorter current wall - its water level is already determined.",
            "Do not forget max(0, ...) - at a wall itself the contribution is 0.",
        ],
        "python": """
class Solution:
    def trap(self, height):
        lo, hi = 0, len(height) - 1
        left_max = right_max = 0
        water = 0
        while lo < hi:
            if height[lo] <= height[hi]:
                if height[lo] >= left_max:
                    left_max = height[lo]
                else:
                    water += left_max - height[lo]
                lo += 1
            else:
                if height[hi] >= right_max:
                    right_max = height[hi]
                else:
                    water += right_max - height[hi]
                hi -= 1
        return water
""",
        "javascript": """
var trap = function(height) {
    let lo = 0, hi = height.length - 1;
    let leftMax = 0, rightMax = 0, water = 0;
    while (lo < hi) {
        if (height[lo] <= height[hi]) {
            if (height[lo] >= leftMax) leftMax = height[lo];
            else water += leftMax - height[lo];
            lo++;
        } else {
            if (height[hi] >= rightMax) rightMax = height[hi];
            else water += rightMax - height[hi];
            hi--;
        }
    }
    return water;
};
""",
        "java": """
class Solution {
    public int trap(int[] height) {
        int lo = 0, hi = height.length - 1;
        int leftMax = 0, rightMax = 0, water = 0;
        while (lo < hi) {
            if (height[lo] <= height[hi]) {
                if (height[lo] >= leftMax) leftMax = height[lo];
                else water += leftMax - height[lo];
                lo++;
            } else {
                if (height[hi] >= rightMax) rightMax = height[hi];
                else water += rightMax - height[hi];
                hi--;
            }
        }
        return water;
    }
}
""",
    },
    "two-sum": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Scan the array once while storing each value's index in a hash map.
2. For every element `x`, check whether `target - x` was already seen.
3. If it was, the stored index and the current index form the answer.
4. Because the complement is looked up **before** inserting `x`, an element can never pair with itself.

Single pass with `O(1)` average lookups - far better than the `O(n^2)` brute force.""",
        "hints": [
            "Store value -> index as you go, not after the loop.",
            "complement = target - nums[i]; if it is in the map you are done.",
            "Insert into the map AFTER checking the complement so you do not reuse the same element.",
        ],
        "python": """
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
        "javascript": """
var twoSum = function(nums, target) {
    const seen = new Map();
    for (let i = 0; i < nums.length; i++) {
        const comp = target - nums[i];
        if (seen.has(comp)) return [seen.get(comp), i];
        seen.set(nums[i], i);
    }
    return [];
};
""",
        "java": """
class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int comp = target - nums[i];
            if (seen.containsKey(comp)) return new int[]{seen.get(comp), i};
            seen.put(nums[i], i);
        }
        return new int[0];
    }
}
""",
    },
    "valid-anagram": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Different lengths can never be anagrams - return `False` immediately.
2. Count character frequencies of `s`, then decrement with `t`.
3. If any count goes negative (or remains nonzero), the multisets differ.

Because only 26 lowercase letters are involved, the count array is fixed size - constant extra space.""",
        "hints": [
            "Length check first - the cheapest possible rejection.",
            "A 26-slot array of counts beats a hash map for lowercase English input.",
            "Increment for one string and decrement for the other; a single array is enough.",
        ],
        "python": """
class Solution:
    def isAnagram(self, s, t):
        if len(s) != len(t):
            return False
        counts = [0] * 26
        for ch in s:
            counts[ord(ch) - 97] += 1
        for ch in t:
            counts[ord(ch) - 97] -= 1
            if counts[ord(ch) - 97] < 0:
                return False
        return True
""",
        "javascript": """
var isAnagram = function(s, t) {
    if (s.length !== t.length) return false;
    const counts = new Array(26).fill(0);
    for (const ch of s) counts[ch.charCodeAt(0) - 97]++;
    for (const ch of t) {
        if (--counts[ch.charCodeAt(0) - 97] < 0) return false;
    }
    return true;
};
""",
        "java": """
class Solution {
    public boolean isAnagram(String s, String t) {
        if (s.length() != t.length()) return false;
        int[] counts = new int[26];
        for (char ch : s.toCharArray()) counts[ch - 'a']++;
        for (char ch : t.toCharArray()) {
            if (--counts[ch - 'a'] < 0) return false;
        }
        return true;
    }
}
""",
    },
    "valid-parentheses": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Push every opening bracket onto a stack.
2. On a closing bracket, the stack top must be its matching opener - pop it; otherwise the string is invalid.
3. At the end the stack must be empty (no unclosed openers remain).

A string is valid iff every closer matched the most recent unmatched opener and nothing was left over.""",
        "hints": [
            "Closers must match the LATEST opener - that is exactly a stack's LIFO order.",
            "A closer arriving with an empty stack is an instant failure (e.g. ')').",
            "Do not forget the final empty-stack check ('((' looks fine mid-scan).",
        ],
        "python": """
class Solution:
    def isValid(self, s):
        pairs = {')': '(', ']': '[', '}': '{'}
        stack = []
        for ch in s:
            if ch in '([{':
                stack.append(ch)
            else:
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()
        return not stack
""",
        "javascript": """
var isValid = function(s) {
    const pairs = { ')': '(', ']': '[', '}': '{' };
    const stack = [];
    for (const ch of s) {
        if (ch === '(' || ch === '[' || ch === '{') stack.push(ch);
        else {
            if (!stack.length || stack[stack.length - 1] !== pairs[ch]) return false;
            stack.pop();
        }
    }
    return stack.length === 0;
};
""",
        "java": """
class Solution {
    public boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char ch : s.toCharArray()) {
            if (ch == '(' || ch == '[' || ch == '{') stack.push(ch);
            else {
                if (stack.isEmpty()) return false;
                char top = stack.pop();
                if (ch == ')' && top != '(') return false;
                if (ch == ']' && top != '[') return false;
                if (ch == '}' && top != '{') return false;
            }
        }
        return stack.isEmpty();
    }
}
""",
    },
    "valid-sudoku": {
        "time": "O(1) - fixed 81 cells",
        "space": "O(1)",
        "explanation": """**Approach**

1. A valid Sudoku requires each digit `1-9` to appear at most once per row, per column, and per 3x3 box.
2. Sweep every cell once; for each filled digit compute its box index `(r // 3) * 3 + c // 3`.
3. Mark `(row, digit)`, `(col, digit)`, and `(box, digit)` in three sets of keys - if any key already exists, the board is invalid.
4. Empty cells (`.`) are skipped.

Constant work because the board is always exactly 9x9.""",
        "hints": [
            "Encode each constraint as a tuple key like (row, digit) in a set.",
            "Box index formula: (r // 3) * 3 + c // 3.",
            "Duplicates only matter for FILLED cells - ignore '.'.",
        ],
        "python": """
class Solution:
    def isValidSudoku(self, board):
        seen = set()
        for r in range(9):
            for c in range(9):
                val = board[r][c]
                if val == '.':
                    continue
                keys = (('row', r, val), ('col', c, val), ('box', (r // 3) * 3 + c // 3, val))
                for key in keys:
                    if key in seen:
                        return False
                    seen.add(key)
        return True
""",
        "javascript": """
var isValidSudoku = function(board) {
    const seen = new Set();
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            const val = board[r][c];
            if (val === '.') continue;
            const keys = [`r${r}${val}`, `c${c}${val}`, `b${Math.floor(r / 3) * 3 + Math.floor(c / 3)}${val}`];
            for (const key of keys) {
                if (seen.has(key)) return false;
                seen.add(key);
            }
        }
    }
    return true;
};
""",
        "java": """
class Solution {
    public boolean isValidSudoku(char[][] board) {
        Set<String> seen = new HashSet<>();
        for (int r = 0; r < 9; r++) {
            for (int c = 0; c < 9; c++) {
                char val = board[r][c];
                if (val == '.') continue;
                if (!seen.add("r" + r + val)) return false;
                if (!seen.add("c" + c + val)) return false;
                if (!seen.add("b" + (r / 3) * 3 + c / 3 + val)) return false;
            }
        }
        return true;
    }
}
""",
    },
    "validate-binary-search-tree": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. Every node must lie inside a **valid range** `(low, high)` inherited from its ancestors.
2. The left child's upper bound becomes the parent's value; the right child's lower bound becomes the parent's value.
3. Recurse with both bounds: if any node falls outside, return `False`.
4. Strict inequality matters - equal values are not allowed in a BST.

An in-order traversal collecting values would also work (must be strictly increasing), but the bounds method prunes early.""",
        "hints": [
            "Pass down both a min and max allowed value - not just one.",
            "Use strict comparisons: left < node < right (duplicates invalid).",
            "Start with (-inf, +inf) at the root.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def isValidBST(self, root):
        def valid(node, low, high):
            if not node:
                return True
            if not (low < node.val < high):
                return False
            return valid(node.left, low, node.val) and valid(node.right, node.val, high)

        return valid(root, float('-inf'), float('inf'))
""",
        "javascript": """
var isValidBST = function(root) {
    const valid = (node, low, high) => {
        if (!node) return true;
        if (!(node.val > low && node.val < high)) return false;
        return valid(node.left, low, node.val) && valid(node.right, node.val, high);
    };
    return valid(root, -Infinity, Infinity);
};
""",
        "java": """
class Solution {
    public boolean isValidBST(TreeNode root) {
        return valid(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    private boolean valid(TreeNode node, long low, long high) {
        if (node == null) return true;
        if (!(node.val > low && node.val < high)) return false;
        return valid(node.left, low, node.val) && valid(node.right, node.val, high);
    }
}
""",
    },
    "word-ladder": {
        "time": "O(M^2 * N)",
        "space": "O(M * N)",
        "explanation": """**Approach**

1. Treat each word as a node; an edge connects two words differing by exactly one character.
2. BFS from `beginWord` tracking the transformation sequence length; the first time `endWord` is reached is the shortest path.
3. To find neighbors efficiently, either compare every word in the set (`O(M)` per word) or pre-index words by their wildcard patterns (`hot` -> `*ot`, `h*t`).
4. Return 0 when `endWord` is not in the dictionary (no ladder exists).

BFS guarantees the first hit is optimal.""",
        "hints": [
            "BFS layer by layer - the depth of the first encounter IS the answer.",
            "The ladder length counts WORDS (beginWord included), so start at 1.",
            "If endWord is missing from wordList, return 0 immediately.",
        ],
        "python": """
from collections import deque

class Solution:
    def ladderLength(self, beginWord, endWord, wordList):
        words = set(wordList)
        if endWord not in words:
            return 0
        queue = deque([(beginWord, 1)])
        seen = {beginWord}
        while queue:
            word, length = queue.popleft()
            for i in range(len(word)):
                for ch in 'abcdefghijklmnopqrstuvwxyz':
                    nxt = word[:i] + ch + word[i + 1:]
                    if nxt == endWord:
                        return length + 1
                    if nxt in words and nxt not in seen:
                        seen.add(nxt)
                        queue.append((nxt, length + 1))
        return 0
""",
        "javascript": """
var ladderLength = function(beginWord, endWord, wordList) {
    const words = new Set(wordList);
    if (!words.has(endWord)) return 0;
    let queue = [[beginWord, 1]];
    const seen = new Set([beginWord]);
    while (queue.length) {
        const [word, length] = queue.shift();
        const chars = word.split('');
        for (let i = 0; i < chars.length; i++) {
            const orig = chars[i];
            for (let c = 97; c <= 122; c++) {
                chars[i] = String.fromCharCode(c);
                const nxt = chars.join('');
                if (nxt === endWord) return length + 1;
                if (words.has(nxt) && !seen.has(nxt)) {
                    seen.add(nxt);
                    queue.push([nxt, length + 1]);
                }
            }
            chars[i] = orig;
        }
    }
    return 0;
};
""",
        "java": """
class Solution {
    public int ladderLength(String beginWord, String endWord, List<String> wordList) {
        Set<String> words = new HashSet<>(wordList);
        if (!words.contains(endWord)) return 0;
        Queue<String[]> queue = new LinkedList<>();
        queue.add(new String[]{beginWord, "1"});
        Set<String> seen = new HashSet<>();
        seen.add(beginWord);
        char[] alphabet = "abcdefghijklmnopqrstuvwxyz".toCharArray();
        while (!queue.isEmpty()) {
            String[] cur = queue.poll();
            String word = cur[0];
            int length = Integer.parseInt(cur[1]);
            char[] chars = word.toCharArray();
            for (int i = 0; i < chars.length; i++) {
                char orig = chars[i];
                for (char c : alphabet) {
                    chars[i] = c;
                    String nxt = new String(chars);
                    if (nxt.equals(endWord)) return length + 1;
                    if (words.contains(nxt) && seen.add(nxt)) {
                        queue.add(new String[]{nxt, String.valueOf(length + 1)});
                    }
                }
                chars[i] = orig;
            }
        }
        return 0;
    }
}
""",
    },
    "word-search": {
        "time": "O(m * n * 4^L)",
        "space": "O(L)",
        "explanation": """**Approach**

1. For every cell that matches `word[0]`, launch a depth-first search for the rest of the word.
2. From a matched cell, explore the four neighbors matching the next character, marking the current cell as visited (e.g. temporarily changing it to `#`) to avoid reusing it.
3. When the matched length equals `len(word)`, the word was found.
4. Unwind the recursion (restore the cell) on backtrack so other paths can still use it.

The `4^L` factor comes from the branching factor over word length `L`.""",
        "hints": [
            "Mark visited cells in place, then restore them when backtracking.",
            "Start a fresh DFS from EVERY cell that matches the first letter.",
            "Early return as soon as one path succeeds.",
        ],
        "python": """
class Solution:
    def exist(self, board, word):
        rows, cols = len(board), len(board[0])

        def dfs(r, c, idx):
            if idx == len(word):
                return True
            if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != word[idx]:
                return False
            saved = board[r][c]
            board[r][c] = '#'
            found = (dfs(r + 1, c, idx + 1) or dfs(r - 1, c, idx + 1)
                     or dfs(r, c + 1, idx + 1) or dfs(r, c - 1, idx + 1))
            board[r][c] = saved
            return found

        for r in range(rows):
            for c in range(cols):
                if dfs(r, c, 0):
                    return True
        return False
""",
        "javascript": """
var exist = function(board, word) {
    const rows = board.length, cols = board[0].length;
    const dfs = (r, c, idx) => {
        if (idx === word.length) return true;
        if (r < 0 || c < 0 || r >= rows || c >= cols || board[r][c] !== word[idx]) return false;
        const saved = board[r][c];
        board[r][c] = '#';
        const found = dfs(r + 1, c, idx + 1) || dfs(r - 1, c, idx + 1)
                   || dfs(r, c + 1, idx + 1) || dfs(r, c - 1, idx + 1);
        board[r][c] = saved;
        return found;
    };
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (dfs(r, c, 0)) return true;
        }
    }
    return false;
};
""",
        "java": """
class Solution {
    public boolean exist(char[][] board, String word) {
        int rows = board.length, cols = board[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (dfs(board, r, c, word, 0)) return true;
            }
        }
        return false;
    }
    private boolean dfs(char[][] b, int r, int c, String w, int idx) {
        if (idx == w.length()) return true;
        if (r < 0 || c < 0 || r >= b.length || c >= b[0].length || b[r][c] != w.charAt(idx)) return false;
        char saved = b[r][c];
        b[r][c] = '#';
        boolean found = dfs(b, r + 1, c, w, idx + 1) || dfs(b, r - 1, c, w, idx + 1)
                     || dfs(b, r, c + 1, w, idx + 1) || dfs(b, r, c - 1, w, idx + 1);
        b[r][c] = saved;
        return found;
    }
}
""",
    },
}
