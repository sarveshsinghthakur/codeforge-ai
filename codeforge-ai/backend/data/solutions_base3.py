"""Real solutions + explanations for base problems (batch 3/4): lru-cache .. roman-to-integer."""

SOLUTIONS = {
    "lru-cache": {
        "time": "O(1) per operation",
        "space": "O(capacity)",
        "explanation": """**Approach**

1. Combine a hash map (key -> node for `O(1)` lookup) with a doubly linked list that tracks recency.
2. The list head holds the most recently used entry; the tail holds the least recently used.
3. `get` looks up the node, detaches it from its current position, and moves it to the front; `put` does the same for the updated key.
4. When capacity is exceeded, evict the node at the tail (least recently used).

Both operations are a hash lookup plus a constant number of pointer rewires, so `O(1)` each.""",
        "hints": [
            "You need BOTH O(1) lookup (hash map) and O(1) reordering (linked list).",
            "A dummy head and tail remove all null checks when moving or evicting nodes.",
            "Always detach a node before reattaching it at the front - including on a get() hit.",
        ],
        "python": """
class Node:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        if key not in self.map:
            return None
        node = self.map[key]
        self._remove(node)
        self._push_front(node)
        return node.val

    def put(self, key, value):
        if key in self.map:
            node = self.map[key]
            node.val = value
            self._remove(node)
            self._push_front(node)
            return
        if len(self.map) >= self.cap:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
        node = Node(key, value)
        self.map[key] = node
        self._push_front(node)
""",
        "javascript": """
var LRUCache = function(capacity) {
    this.cap = capacity;
    this.map = new Map();
    this.head = { key: 0, val: 0 };
    this.tail = { key: 0, val: 0 };
    this.head.next = this.tail;
    this.tail.prev = this.head;
};

LRUCache.prototype._remove = function(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
};

LRUCache.prototype._pushFront = function(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
};

LRUCache.prototype.get = function(key) {
    if (!this.map.has(key)) return null;
    const node = this.map.get(key);
    this._remove(node);
    this._pushFront(node);
    return node.val;
};

LRUCache.prototype.put = function(key, value) {
    if (this.map.has(key)) {
        const node = this.map.get(key);
        node.val = value;
        this._remove(node);
        this._pushFront(node);
        return;
    }
    if (this.map.size >= this.cap) {
        const lru = this.tail.prev;
        this._remove(lru);
        this.map.delete(lru.key);
    }
    const node = { key, val: value };
    this.map.set(key, node);
    this._pushFront(node);
};
""",
        "java": """
class LRUCache {
    private int cap;
    private Map<Integer, Node> map = new HashMap<>();
    private Node head = new Node(0, 0);
    private Node tail = new Node(0, 0);

    private static class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }

    public LRUCache(int capacity) {
        cap = capacity;
        head.next = tail;
        tail.prev = head;
    }

    private void remove(Node n) {
        n.prev.next = n.next;
        n.next.prev = n.prev;
    }

    private void pushFront(Node n) {
        n.next = head.next;
        n.prev = head;
        head.next.prev = n;
        head.next = n;
    }

    public int get(int key) {
        if (!map.containsKey(key)) return -1;
        Node n = map.get(key);
        remove(n);
        pushFront(n);
        return n.val;
    }

    public void put(int key, int value) {
        if (map.containsKey(key)) {
            Node n = map.get(key);
            n.val = value;
            remove(n);
            pushFront(n);
            return;
        }
        if (map.size() >= cap) {
            Node lru = tail.prev;
            remove(lru);
            map.remove(lru.key);
        }
        Node n = new Node(key, value);
        map.put(key, n);
        pushFront(n);
    }
}
""",
    },
    "majority-element": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Boyer-Moore voting: keep a candidate and a counter.
2. On a matching element increment the counter; on a mismatch decrement it.
3. When the counter hits zero, replace the candidate with the current element and reset the counter to 1.
4. Because the majority element occupies more than half the array, it always survives - no second pass is needed.

One pass, constant memory, and no sorting.""",
        "hints": [
            "Think of mismatched pairs cancelling each other out.",
            "When the counter reaches 0, the NEXT element becomes the new candidate.",
            "The guarantee 'appears more than n/2 times' is what makes a single pass sufficient.",
        ],
        "python": """
class Solution:
    def majorityElement(self, nums):
        candidate = None
        count = 0
        for n in nums:
            if count == 0:
                candidate = n
                count = 1
            elif n == candidate:
                count += 1
            else:
                count -= 1
        return candidate
""",
        "javascript": """
var majorityElement = function(nums) {
    let candidate = null, count = 0;
    for (const n of nums) {
        if (count === 0) { candidate = n; count = 1; }
        else if (n === candidate) count++;
        else count--;
    }
    return candidate;
};
""",
        "java": """
class Solution {
    public int majorityElement(int[] nums) {
        Integer candidate = null;
        int count = 0;
        for (int n : nums) {
            if (count == 0) { candidate = n; count = 1; }
            else if (n == candidate) count++;
            else count--;
        }
        return candidate;
    }
}
""",
    },
    "maximum-depth-of-binary-tree": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. The depth of a node is `1 + max(depth(left), depth(right))`.
2. An empty subtree has depth 0, which is the recursion base case.
3. A single post-order DFS computes the depths bottom-up; the maximum depth is whatever the root returns.

Every node contributes a constant amount of work; recursion depth equals the tree height.""",
        "hints": [
            "Null subtree depth is 0 - that is your base case.",
            "Combine the results from BOTH children before returning.",
            "An iterative level-order traversal also works: depth = number of levels.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def maxDepth(self, root):
        if not root:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
""",
        "javascript": """
var maxDepth = function(root) {
    if (!root) return 0;
    return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
};
""",
        "java": """
class Solution {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }
}
""",
    },
    "maximum-product-subarray": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Track both the running **maximum** and **minimum** product ending at the current index: negatives can flip roles.
2. At each step compute `hi = max(x, hi*x, lo*x)` and `lo = min(x, hi_old*x, lo_old*x)` (use the previous values for both).
3. The answer is the largest `hi` seen anywhere - a maximum can also start fresh at any element.
4. Zeros naturally reset both values to the current element.

Carrying the minimum alongside the maximum is the key insight for handling an even count of negatives.""",
        "hints": [
            "A negative number turns the previous minimum into the new maximum.",
            "Use the OLD hi and lo when computing the new pair - compute both before overwriting.",
            "A zero wipes the window; treat the zero itself as a fresh start.",
        ],
        "python": """
class Solution:
    def maxProduct(self, nums):
        best = hi = lo = nums[0]
        for x in nums[1:]:
            cands = (x, hi * x, lo * x)
            hi = max(cands)
            lo = min(cands)
            best = max(best, hi)
        return best
""",
        "javascript": """
var maxProduct = function(nums) {
    let best = nums[0], hi = nums[0], lo = nums[0];
    for (let i = 1; i < nums.length; i++) {
        const x = nums[i];
        const cands = [x, hi * x, lo * x];
        hi = Math.max(...cands);
        lo = Math.min(...cands);
        best = Math.max(best, hi);
    }
    return best;
};
""",
        "java": """
class Solution {
    public int maxProduct(int[] nums) {
        int best = nums[0], hi = nums[0], lo = nums[0];
        for (int i = 1; i < nums.length; i++) {
            int x = nums[i];
            int a = x, b = hi * x, c = lo * x;
            hi = Math.max(a, Math.max(b, c));
            lo = Math.min(a, Math.min(b, c));
            best = Math.max(best, hi);
        }
        return best;
    }
}
""",
    },
    "maximum-subarray": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Kadane's algorithm: `best_ending_here = max(x, best_ending_here + x)` - either extend the previous subarray or start fresh at `x`.
2. A running global maximum records the best of those values.
3. Starting fresh whenever the running sum turns negative discards a prefix that can only drag the sum down.

The equivalent formulation `dp[i] = max(nums[i], dp[i-1] + nums[i])` is classic 1-D DP, but only two variables are needed.""",
        "hints": [
            "Either extend the current subarray or start a new one at the current element.",
            "Every element must belong to the subarray, so the answer is at least max(nums).",
            "Initialize both variables to nums[0] - all-negative arrays are the tricky case.",
        ],
        "python": """
class Solution:
    def maxSubArray(self, nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best
""",
        "javascript": """
var maxSubArray = function(nums) {
    let best = nums[0], cur = nums[0];
    for (let i = 1; i < nums.length; i++) {
        cur = Math.max(nums[i], cur + nums[i]);
        best = Math.max(best, cur);
    }
    return best;
};
""",
        "java": """
class Solution {
    public int maxSubArray(int[] nums) {
        int best = nums[0], cur = nums[0];
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(nums[i], cur + nums[i]);
            best = Math.max(best, cur);
        }
        return best;
    }
}
""",
    },
    "median-of-two-sorted-arrays": {
        "time": "O(log(min(m, n)))",
        "space": "O(1)",
        "explanation": """**Approach**

1. Binary search on the **smaller** array for the partition point `i`; the other partition is forced to `(m + n + 1) // 2 - j`.
2. Check the cross conditions: `max_left_1 <= min_right_2` and `max_left_2 <= min_right_1`.
3. If satisfied: odd total length returns `max(max_left_1, max_left_2)`, even returns their average with the two minimums on the right.
4. If `max_left_1 > min_right_2`, move `i` left; otherwise move `i` right.

Only the smaller array is searched, so the bound is `O(log(min(m, n)))`.""",
        "hints": [
            "Binary search over the partition index of the SHORTER array.",
            "Everything left of the partition must be <= everything right of it on both sides.",
            "Handle the edge partitions (i = 0 or i = m) with +/- infinity sentinels.",
        ],
        "python": """
class Solution:
    def findMedianSortedArrays(self, nums1, nums2):
        if len(nums1) > len(nums2):
            nums1, nums2 = nums2, nums1
        m, n = len(nums1), len(nums2)
        lo, hi = 0, m
        while lo <= hi:
            i = (lo + hi) // 2
            j = (m + n + 1) // 2 - i
            a1 = float('-inf') if i == 0 else nums1[i - 1]
            a2 = float('inf') if i == m else nums1[i]
            b1 = float('-inf') if j == 0 else nums2[j - 1]
            b2 = float('inf') if j == n else nums2[j]
            if a1 <= b2 and b1 <= a2:
                if (m + n) % 2 == 1:
                    return float(max(a1, b1))
                return (max(a1, b1) + min(a2, b2)) / 2.0
            if a1 > b2:
                hi = i - 1
            else:
                lo = i + 1
        return 0.0
""",
        "javascript": """
var findMedianSortedArrays = function(nums1, nums2) {
    if (nums1.length > nums2.length) [nums1, nums2] = [nums2, nums1];
    const m = nums1.length, n = nums2.length;
    let lo = 0, hi = m;
    while (lo <= hi) {
        const i = (lo + hi) >> 1;
        const j = ((m + n + 1) >> 1) - i;
        const a1 = i === 0 ? -Infinity : nums1[i - 1];
        const a2 = i === m ? Infinity : nums1[i];
        const b1 = j === 0 ? -Infinity : nums2[j - 1];
        const b2 = j === n ? Infinity : nums2[j];
        if (a1 <= b2 && b1 <= a2) {
            if ((m + n) % 2 === 1) return Math.max(a1, b1);
            return (Math.max(a1, b1) + Math.min(a2, b2)) / 2;
        }
        if (a1 > b2) hi = i - 1;
        else lo = i + 1;
    }
    return 0;
};
""",
        "java": """
class Solution {
    public double findMedianSortedArrays(int[] nums1, int[] nums2) {
        if (nums1.length > nums2.length) return findMedianSortedArrays(nums2, nums1);
        int m = nums1.length, n = nums2.length;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int i = lo + (hi - lo) / 2;
            int j = (m + n + 1) / 2 - i;
            int a1 = i == 0 ? Integer.MIN_VALUE : nums1[i - 1];
            int a2 = i == m ? Integer.MAX_VALUE : nums1[i];
            int b1 = j == 0 ? Integer.MIN_VALUE : nums2[j - 1];
            int b2 = j == n ? Integer.MAX_VALUE : nums2[j];
            if (a1 <= b2 && b1 <= a2) {
                if ((m + n) % 2 == 1) return Math.max(a1, b1);
                return (Math.max(a1, b1) + Math.min(a2, b2)) / 2.0;
            }
            if (a1 > b2) hi = i - 1;
            else lo = i + 1;
        }
        return 0;
    }
}
""",
    },
    "meeting-rooms-ii": {
        "time": "O(n log n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Split every meeting into a **start** event and an **end** event and sort all events.
2. Sweep in time order: a start increments the running room count, an end decrements it.
3. Process ends before starts at the same timestamp so back-to-back meetings reuse the same room.
4. The maximum count seen is the minimum number of rooms needed.

Sorting dominates the cost: `O(n log n)`.""",
        "hints": [
            "Two sorted arrays of starts and ends work too: walk them side by side.",
            "A meeting ending at time t frees its room for one starting at t - process ends first on ties.",
            "The answer is the PEAK concurrent count, not the final count (which is always 0).",
        ],
        "python": """
class Solution:
    def minMeetingRooms(self, intervals):
        starts = sorted(s for s, e in intervals)
        ends = sorted(e for s, e in intervals)
        i = j = 0
        rooms = peak = 0
        while i < len(starts):
            if starts[i] < ends[j]:
                rooms += 1
                peak = max(peak, rooms)
                i += 1
            else:
                rooms -= 1
                j += 1
        return peak
""",
        "javascript": """
var minMeetingRooms = function(intervals) {
    const starts = intervals.map(v => v[0]).sort((a, b) => a - b);
    const ends = intervals.map(v => v[1]).sort((a, b) => a - b);
    let i = 0, j = 0, rooms = 0, peak = 0;
    while (i < starts.length) {
        if (starts[i] < ends[j]) {
            rooms++;
            peak = Math.max(peak, rooms);
            i++;
        } else {
            rooms--;
            j++;
        }
    }
    return peak;
};
""",
        "java": """
class Solution {
    public int minMeetingRooms(int[][] intervals) {
        int n = intervals.length;
        int[] starts = new int[n];
        int[] ends = new int[n];
        for (int i = 0; i < n; i++) { starts[i] = intervals[i][0]; ends[i] = intervals[i][1]; }
        Arrays.sort(starts);
        Arrays.sort(ends);
        int i = 0, j = 0, rooms = 0, peak = 0;
        while (i < n) {
            if (starts[i] < ends[j]) {
                rooms++;
                peak = Math.max(peak, rooms);
                i++;
            } else {
                rooms--;
                j++;
            }
        }
        return peak;
    }
}
""",
    },
    "merge-intervals": {
        "time": "O(n log n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Sort intervals by start time so overlapping ones become adjacent.
2. Keep the last merged interval `cur`; for the next interval `it`:
   - If `it.start <= cur.end` they overlap - extend `cur.end = max(cur.end, it.end)`.
   - Otherwise append `cur` to the result and start a new one from `it`.
3. Flush the final `cur` after the loop.

Sorting is the dominant `O(n log n)` cost; the merge sweep itself is linear.""",
        "hints": [
            "Sorting by start is what turns the problem into a single linear sweep.",
            "Compare against the END of the LAST merged interval, not the previous input interval.",
            "Nested intervals need max(end), not just assignment.",
        ],
        "python": """
class Solution:
    def merge(self, intervals):
        intervals.sort(key=lambda x: x[0])
        res = []
        for it in intervals:
            if res and it[0] <= res[-1][1]:
                res[-1][1] = max(res[-1][1], it[1])
            else:
                res.append([it[0], it[1]])
        return res
""",
        "javascript": """
var merge = function(intervals) {
    intervals.sort((a, b) => a[0] - b[0]);
    const res = [];
    for (const it of intervals) {
        if (res.length && it[0] <= res[res.length - 1][1]) {
            res[res.length - 1][1] = Math.max(res[res.length - 1][1], it[1]);
        } else {
            res.push([it[0], it[1]]);
        }
    }
    return res;
};
""",
        "java": """
class Solution {
    public int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
        List<int[]> res = new ArrayList<>();
        for (int[] it : intervals) {
            if (!res.isEmpty() && it[0] <= res.get(res.size() - 1)[1]) {
                int[] cur = res.get(res.size() - 1);
                cur[1] = Math.max(cur[1], it[1]);
            } else {
                res.add(new int[]{it[0], it[1]});
            }
        }
        return res.toArray(new int[0][]);
    }
}
""",
    },
    "merge-k-sorted-lists": {
        "time": "O(N log k)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Repeatedly merge two lists until one remains: each merge pass combines pairs of lists.
2. Merging two sorted lists of total length `L` costs `O(L)`; there are `log k` rounds of merging, and each element is touched once per round.
3. Total work is `O(N log k)` where `N` is the total number of nodes.

(A min-heap over the current heads also achieves `O(N log k)`; the pairwise approach uses no extra heap memory.)""",
        "hints": [
            "Pairwise merging turns k lists into k/2, then k/4, ... just like merge sort.",
            "Handle odd counts (the last list is carried over unchanged).",
            "The two-list merge is the same code as merge-two-sorted-lists - reuse it.",
        ],
        "python": """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def mergeKLists(self, lists):
        def build(vals):
            dummy = ListNode(0)
            tail = dummy
            for v in vals:
                tail.next = ListNode(v)
                tail = tail.next
            return dummy.next

        def merge_two(a, b):
            dummy = ListNode(0)
            tail = dummy
            while a and b:
                if a.val <= b.val:
                    tail.next = a
                    a = a.next
                else:
                    tail.next = b
                    b = b.next
                tail = tail.next
            tail.next = a if a else b
            return dummy.next

        if not lists:
            return None
        lists = [build(v) if isinstance(v, list) else v for v in lists]
        while len(lists) > 1:
            merged = []
            for i in range(0, len(lists), 2):
                a = lists[i]
                b = lists[i + 1] if i + 1 < len(lists) else None
                merged.append(merge_two(a, b))
            lists = merged
        return lists[0]
""",
        "javascript": """
var mergeKLists = function(lists) {
    const build = (vals) => {
        const dummy = new ListNode(0);
        let tail = dummy;
        for (const v of vals) {
            tail.next = new ListNode(v);
            tail = tail.next;
        }
        return dummy.next;
    };
    const mergeTwo = (a, b) => {
        const dummy = new ListNode(0);
        let tail = dummy;
        while (a && b) {
            if (a.val <= b.val) { tail.next = a; a = a.next; }
            else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = a || b;
        return dummy.next;
    };
    if (!lists || lists.length === 0) return null;
    let arr = lists.map((v) => (Array.isArray(v) ? build(v) : v));
    while (arr.length > 1) {
        const merged = [];
        for (let i = 0; i < arr.length; i += 2) {
            merged.push(mergeTwo(arr[i], i + 1 < arr.length ? arr[i + 1] : null));
        }
        arr = merged;
    }
    return arr[0];
};
""",
        "java": """
class Solution {
    public ListNode mergeKLists(ListNode[] lists) {
        if (lists == null || lists.length == 0) return null;
        int interval = 1;
        ListNode[] arr = lists;
        while (arr.length > 1) {
            ListNode[] merged = new ListNode[(arr.length + 1) / 2];
            for (int i = 0, k = 0; i < arr.length; i += 2, k++) {
                ListNode b = i + 1 < arr.length ? arr[i + 1] : null;
                merged[k] = mergeTwo(arr[i], b);
            }
            arr = merged;
        }
        return arr[0];
    }
    private ListNode mergeTwo(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0), tail = dummy;
        while (a != null && b != null) {
            if (a.val <= b.val) { tail.next = a; a = a.next; }
            else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = a != null ? a : b;
        return dummy.next;
    }
}
""",
    },
    "merge-two-sorted-lists": {
        "time": "O(m + n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. A dummy head makes appending uniform; a tail pointer tracks where to attach the next node.
2. Compare the heads of both lists and attach the smaller one, advancing only that pointer.
3. When one list is exhausted, attach the entire remainder of the other.
4. Return `dummy.next`.

Every node is visited once, and only the existing nodes are reused (no new allocation except the dummy).""",
        "hints": [
            "A dummy node avoids a special case for the first attached element.",
            "Always advance only the pointer whose node you just attached.",
            "Do not forget the tail: one list may finish while the other still has nodes.",
        ],
        "python": """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def mergeTwoLists(self, list1, list2):
        dummy = ListNode(0)
        tail = dummy
        while list1 and list2:
            if list1.val <= list2.val:
                tail.next = list1
                list1 = list1.next
            else:
                tail.next = list2
                list2 = list2.next
            tail = tail.next
        tail.next = list1 if list1 else list2
        return dummy.next
""",
        "javascript": """
var mergeTwoLists = function(list1, list2) {
    const dummy = new ListNode(0);
    let tail = dummy;
    while (list1 && list2) {
        if (list1.val <= list2.val) { tail.next = list1; list1 = list1.next; }
        else { tail.next = list2; list2 = list2.next; }
        tail = tail.next;
    }
    tail.next = list1 || list2;
    return dummy.next;
};
""",
        "java": """
class Solution {
    public ListNode mergeTwoLists(ListNode list1, ListNode list2) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (list1 != null && list2 != null) {
            if (list1.val <= list2.val) { tail.next = list1; list1 = list1.next; }
            else { tail.next = list2; list2 = list2.next; }
            tail = tail.next;
        }
        tail.next = list1 != null ? list1 : list2;
        return dummy.next;
    }
}
""",
    },
    "missing-number": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. The array holds `n` of the `n + 1` numbers in `[0, n]`.
2. The XOR of `0..n` equals a known value; XOR it with every array element and index - everything present twice cancels, leaving the missing number.
3. Equivalently: `sum(0..n) - sum(array)` (both are `O(n)`, but XOR avoids overflow concerns).

Either way, one pass and constant space.""",
        "hints": [
            "XOR pairs cancel: x ^ x = 0, and 0 ^ x = x.",
            "XOR all indices 0..n together with all values.",
            "Gauss's sum formula works too, but watch integer size in other languages.",
        ],
        "python": """
class Solution:
    def missingNumber(self, nums):
        xor = len(nums)
        for i, n in enumerate(nums):
            xor ^= i ^ n
        return xor
""",
        "javascript": """
var missingNumber = function(nums) {
    let xor = nums.length;
    for (let i = 0; i < nums.length; i++) xor ^= i ^ nums[i];
    return xor;
};
""",
        "java": """
class Solution {
    public int missingNumber(int[] nums) {
        int xor = nums.length;
        for (int i = 0; i < nums.length; i++) xor ^= i ^ nums[i];
        return xor;
    }
}
""",
    },
    "n-queens": {
        "time": "O(n!)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Place queens row by row; once a row is fixed, only the column choice remains.
2. Track occupied columns and both diagonal directions (`row - col` constant along one diagonal, `row + col` along the other).
3. At each row try every column that is free on all three sets, place a queen, recurse, then undo (backtrack).
4. When the row index reaches `n`, render the board as `n` strings of `n` characters.

Diagonal checks collapse from `O(n)` scans into `O(1)` set lookups.""",
        "hints": [
            "Three constraints: column, 'down-right' diagonal (row - col), 'down-left' diagonal (row + col).",
            "Always undo the placement after the recursive call returns.",
            "Rendering: put 'Q' at the chosen column, '.' elsewhere, then join.",
        ],
        "python": """
class Solution:
    def solveNQueens(self, n):
        res = []
        cols, diag1, diag2 = set(), set(), set()
        board = [['.'] * n for _ in range(n)]

        def dfs(row):
            if row == n:
                res.append([''.join(r) for r in board])
                return
            for col in range(n):
                if col in cols or (row - col) in diag1 or (row + col) in diag2:
                    continue
                cols.add(col)
                diag1.add(row - col)
                diag2.add(row + col)
                board[row][col] = 'Q'
                dfs(row + 1)
                board[row][col] = '.'
                cols.remove(col)
                diag1.remove(row - col)
                diag2.remove(row + col)

        dfs(0)
        return res
""",
        "javascript": """
var solveNQueens = function(n) {
    const res = [];
    const cols = new Set(), diag1 = new Set(), diag2 = new Set();
    const board = Array.from({ length: n }, () => new Array(n).fill('.'));
    const dfs = (row) => {
        if (row === n) { res.push(board.map(r => r.join(''))); return; }
        for (let col = 0; col < n; col++) {
            if (cols.has(col) || diag1.has(row - col) || diag2.has(row + col)) continue;
            cols.add(col); diag1.add(row - col); diag2.add(row + col);
            board[row][col] = 'Q';
            dfs(row + 1);
            board[row][col] = '.';
            cols.delete(col); diag1.delete(row - col); diag2.delete(row + col);
        }
    };
    dfs(0);
    return res;
};
""",
        "java": """
class Solution {
    private List<List<String>> res = new ArrayList<>();
    private Set<Integer> cols = new HashSet<>(), d1 = new HashSet<>(), d2 = new HashSet<>();
    private int n;
    public List<List<String>> solveNQueens(int n) {
        this.n = n;
        char[][] board = new char[n][n];
        for (char[] row : board) Arrays.fill(row, '.');
        dfs(0, board);
        return res;
    }
    private void dfs(int row, char[][] board) {
        if (row == n) {
            List<String> sol = new ArrayList<>();
            for (char[] r : board) sol.add(new String(r));
            res.add(sol);
            return;
        }
        for (int col = 0; col < n; col++) {
            if (cols.contains(col) || d1.contains(row - col) || d2.contains(row + col)) continue;
            cols.add(col); d1.add(row - col); d2.add(row + col);
            board[row][col] = 'Q';
            dfs(row + 1, board);
            board[row][col] = '.';
            cols.remove(col); d1.remove(row - col); d2.remove(row + col);
        }
    }
}
""",
    },
    "number-of-islands": {
        "time": "O(m * n)",
        "space": "O(m * n) worst",
        "explanation": """**Approach**

1. Scan every cell; when an unvisited `'1'` is found, an island starts - increment the counter.
2. Flood-fill from that cell (DFS/BFS) marking every connected land cell as visited (turn it into water or use a visited set).
3. The flood guarantees all cells of the island are counted exactly once.

Every cell is examined a constant number of times, giving a linear pass over the grid.""",
        "hints": [
            "Each time you hit a '1' you have discovered a NEW island - then sink it entirely.",
            "Mark visited cells in-place ('1' -> '0') to avoid a separate visited matrix.",
            "Four-directional connectivity only (not diagonals).",
        ],
        "python": """
class Solution:
    def numIslands(self, grid):
        if not grid:
            return 0
        rows, cols = len(grid), len(grid[0])
        count = 0

        def sink(r, c):
            if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != '1':
                return
            grid[r][c] = '0'
            sink(r + 1, c)
            sink(r - 1, c)
            sink(r, c + 1)
            sink(r, c - 1)

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == '1':
                    count += 1
                    sink(r, c)
        return count
""",
        "javascript": """
var numIslands = function(grid) {
    if (!grid.length) return 0;
    const rows = grid.length, cols = grid[0].length;
    let count = 0;
    const sink = (r, c) => {
        if (r < 0 || c < 0 || r >= rows || c >= cols || grid[r][c] !== '1') return;
        grid[r][c] = '0';
        sink(r + 1, c); sink(r - 1, c); sink(r, c + 1); sink(r, c - 1);
    };
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (grid[r][c] === '1') { count++; sink(r, c); }
        }
    }
    return count;
};
""",
        "java": """
class Solution {
    public int numIslands(char[][] grid) {
        if (grid.length == 0) return 0;
        int rows = grid.length, cols = grid[0].length, count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == '1') { count++; sink(grid, r, c); }
            }
        }
        return count;
    }
    private void sink(char[][] g, int r, int c) {
        if (r < 0 || c < 0 || r >= g.length || c >= g[0].length || g[r][c] != '1') return;
        g[r][c] = '0';
        sink(g, r + 1, c); sink(g, r - 1, c); sink(g, r, c + 1); sink(g, r, c - 1);
    }
}
""",
    },
    "palindrome-number": {
        "time": "O(log10(x))",
        "space": "O(1)",
        "explanation": """**Approach**

1. Negative numbers are never palindromes (the leading `-` has no mirror), so reject them immediately.
2. Build the reversed number digit by digit (`rev = rev * 10 + x % 10`, `x //= 10`) and compare with the original.
3. Only half the digits need to be reversed: once `rev >= x` the midpoint has been passed; for even lengths compare `rev == x`, for odd lengths compare `rev // 10 == x` (the middle digit is ignored).

This avoids turning the number into a string.""",
        "hints": [
            "Reject negatives up front.",
            "Reversing HALF the digits is enough and avoids integer overflow in fixed-width languages.",
            "After the loop compare either rev == x (even digits) or rev // 10 == x (odd digits).",
        ],
        "python": """
class Solution:
    def isPalindrome(self, x):
        if x < 0 or (x % 10 == 0 and x != 0):
            return False
        rev = 0
        while x > rev:
            rev = rev * 10 + x % 10
            x //= 10
        return x == rev or x == rev // 10
""",
        "javascript": """
var isPalindrome = function(x) {
    if (x < 0 || (x % 10 === 0 && x !== 0)) return false;
    let rev = 0;
    while (x > rev) {
        rev = rev * 10 + (x % 10);
        x = Math.floor(x / 10);
    }
    return x === rev || x === Math.floor(rev / 10);
};
""",
        "java": """
class Solution {
    public boolean isPalindrome(int x) {
        if (x < 0 || (x % 10 == 0 && x != 0)) return false;
        int rev = 0;
        while (x > rev) {
            rev = rev * 10 + x % 10;
            x /= 10;
        }
        return x == rev || x == rev / 10;
    }
}
""",
    },
    "plus-one": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Start from the last digit and add 1.
2. If the digit becomes 10, set it to 0 and carry 1 to the next digit on the left.
3. If the loop finishes with a carry still pending (all digits were 9), a new leading `1` must be prepended.

The in-place update only grows the array in the all-nines case.""",
        "hints": [
            "Work right to left - that is the direction carries propagate.",
            "9 + 1 = 10: write 0 and keep the carry going.",
            "All nines (999 -> 1000) needs a brand-new first element.",
        ],
        "python": """
class Solution:
    def plusOne(self, digits):
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] < 9:
                digits[i] += 1
                return digits
            digits[i] = 0
        return [1] + digits
""",
        "javascript": """
var plusOne = function(digits) {
    for (let i = digits.length - 1; i >= 0; i--) {
        if (digits[i] < 9) { digits[i]++; return digits; }
        digits[i] = 0;
    }
    return [1, ...digits];
};
""",
        "java": """
class Solution {
    public int[] plusOne(int[] digits) {
        for (int i = digits.length - 1; i >= 0; i--) {
            if (digits[i] < 9) { digits[i]++; return digits; }
            digits[i] = 0;
        }
        int[] res = new int[digits.length + 1];
        res[0] = 1;
        return res;
    }
}
""",
    },
    "power-of-two": {
        "time": "O(1)",
        "space": "O(1)",
        "explanation": """**Approach**

1. A power of two in binary is a single `1` followed by all zeros (`1`, `10`, `100`, ...).
2. `n & (n - 1)` clears the lowest set bit; for a power of two that leaves exactly `0`.
3. So `n > 0 and n & (n - 1) == 0` is a complete characterization.

Alternatives: check that `n` divides `2^60`, or shift right until zero counting steps.""",
        "hints": [
            "n & (n - 1) removes the lowest 1-bit - powers of two only have one.",
            "Do not forget n = 0 and negative numbers: neither is a power of two.",
            "A one-liner: return n > 0 and (n & (n - 1)) == 0.",
        ],
        "python": """
class Solution:
    def isPowerOfTwo(self, n):
        return n > 0 and (n & (n - 1)) == 0
""",
        "javascript": """
var isPowerOfTwo = function(n) {
    return n > 0 && (n & (n - 1)) === 0;
};
""",
        "java": """
class Solution {
    public boolean isPowerOfTwo(int n) {
        return n > 0 && (n & (n - 1)) == 0;
    }
}
""",
    },
    "product-of-array-except-self": {
        "time": "O(n)",
        "space": "O(1) extra",
        "explanation": """**Approach**

1. `answer[i]` must equal `product(nums[0..i-1]) * product(nums[i+1..n-1])`.
2. Left pass: sweep left to right keeping a running prefix product, writing it into `answer[i]`.
3. Right pass: sweep right to left with a running suffix product, multiplying it into `answer[i]`.
4. No division is used, so zeros and duplicate values are handled naturally.

Two linear passes with only constant extra memory (the output array does not count).""",
        "hints": [
            "Build the prefix products first, then multiply the suffixes on top.",
            "Division fails when the array contains a 0 - avoid it entirely.",
            "The right pass can write directly into the output instead of a second array.",
        ],
        "python": """
class Solution:
    def productExceptSelf(self, nums):
        n = len(nums)
        answer = [1] * n
        prefix = 1
        for i in range(n):
            answer[i] = prefix
            prefix *= nums[i]
        suffix = 1
        for i in range(n - 1, -1, -1):
            answer[i] *= suffix
            suffix *= nums[i]
        return answer
""",
        "javascript": """
var productExceptSelf = function(nums) {
    const n = nums.length;
    const answer = new Array(n).fill(1);
    let prefix = 1;
    for (let i = 0; i < n; i++) {
        answer[i] = prefix;
        prefix *= nums[i];
    }
    let suffix = 1;
    for (let i = n - 1; i >= 0; i--) {
        answer[i] *= suffix;
        suffix *= nums[i];
    }
    return answer;
};
""",
        "java": """
class Solution {
    public int[] productExceptSelf(int[] nums) {
        int n = nums.length;
        int[] answer = new int[n];
        int prefix = 1;
        for (int i = 0; i < n; i++) {
            answer[i] = prefix;
            prefix *= nums[i];
        }
        int suffix = 1;
        for (int i = n - 1; i >= 0; i--) {
            answer[i] *= suffix;
            suffix *= nums[i];
        }
        return answer;
    }
}
""",
    },
    "regular-expression-matching": {
        "time": "O(m * n)",
        "space": "O(m * n)",
        "explanation": """**Approach**

1. `dp[i][j]` is whether `s[:i]` matches `p[:j]`.
2. Base: an empty string matches a pattern of only `x*` pairs (`dp[0][j] = dp[0][j-2]` when `p[j-1] == '*'`).
3. For a normal character: `dp[i][j] = dp[i-1][j-1]` if `s[i-1] == p[j-1]` or `p[j-1] == '.'`.
4. For `*`: either **skip** the pair (`dp[i][j-2]`) or **use it once** if the preceding character matches `s[i-1]` (`dp[i-1][j]`).

`.` matches any single character; `*` matches zero or more of the previous token - it never stands alone.""",
        "hints": [
            "Treat each 'c*' as ONE token of the pattern.",
            "'Skip' means the preceding element appears zero times: dp[i][j-2].",
            "'Consume' s[i-1] only if it matches the character before '*'.",
        ],
        "python": """
class Solution:
    def isMatch(self, s, p):
        m, n = len(s), len(p)
        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = True
        for j in range(2, n + 1):
            if p[j - 1] == '*':
                dp[0][j] = dp[0][j - 2]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if p[j - 1] == '*':
                    dp[i][j] = dp[i][j - 2]
                    if p[j - 2] == '.' or p[j - 2] == s[i - 1]:
                        dp[i][j] = dp[i][j] or dp[i - 1][j]
                elif p[j - 1] == '.' or p[j - 1] == s[i - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
        return dp[m][n]
""",
        "javascript": """
var isMatch = function(s, p) {
    const m = s.length, n = p.length;
    const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(false));
    dp[0][0] = true;
    for (let j = 2; j <= n; j++) if (p[j - 1] === '*') dp[0][j] = dp[0][j - 2];
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (p[j - 1] === '*') {
                dp[i][j] = dp[i][j - 2];
                if (p[j - 2] === '.' || p[j - 2] === s[i - 1]) dp[i][j] = dp[i][j] || dp[i - 1][j];
            } else if (p[j - 1] === '.' || p[j - 1] === s[i - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            }
        }
    }
    return dp[m][n];
};
""",
        "java": """
class Solution {
    public boolean isMatch(String s, String p) {
        int m = s.length(), n = p.length();
        boolean[][] dp = new boolean[m + 1][n + 1];
        dp[0][0] = true;
        for (int j = 2; j <= n; j++) if (p.charAt(j - 1) == '*') dp[0][j] = dp[0][j - 2];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (p.charAt(j - 1) == '*') {
                    dp[i][j] = dp[i][j - 2];
                    char pre = p.charAt(j - 2);
                    if (pre == '.' || pre == s.charAt(i - 1)) dp[i][j] |= dp[i - 1][j];
                } else if (p.charAt(j - 1) == '.' || p.charAt(j - 1) == s.charAt(i - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                }
            }
        }
        return dp[m][n];
    }
}
""",
    },
    "reverse-string": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Two pointers start at both ends of the character array.
2. Swap the characters they point at, then move both inward.
3. Stop when the pointers meet - the whole array is reversed in place.
4. Return the (now reversed) array so the caller can compare it directly.""",
        "hints": [
            "Swap lo and hi, then lo++ and hi--.",
            "Only iterate up to len/2 - otherwise you swap everything back.",
            "Swap in place, then return the array - the judge compares the returned array.",
        ],
        "python": """
class Solution:
    def reverseString(self, s):
        lo, hi = 0, len(s) - 1
        while lo < hi:
            s[lo], s[hi] = s[hi], s[lo]
            lo += 1
            hi -= 1
        return s
""",
        "javascript": """
var reverseString = function(s) {
    let lo = 0, hi = s.length - 1;
    while (lo < hi) {
        const t = s[lo];
        s[lo] = s[hi];
        s[hi] = t;
        lo++;
        hi--;
    }
    return s;
};
""",
        "java": """
class Solution {
    public char[] reverseString(char[] s) {
        int lo = 0, hi = s.length - 1;
        while (lo < hi) {
            char t = s[lo];
            s[lo] = s[hi];
            s[hi] = t;
            lo++;
            hi--;
        }
        return s;
    }
}
""",
    },
    "roman-to-integer": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Map each symbol to its value (I=1, V=5, X=10, ...).
2. Scan left to right: normally **add** the current value.
3. If the current value is smaller than the next one (as in `IV` or `IX`), it is a subtractive pair - **subtract** it instead.
4. The final `V`/`I` etc. at the end has no successor, so the loop's last iteration simply adds it.

This single rule handles every subtractive combination (`IV`, `IX`, `XL`, `XC`, `CD`, `CM`).""",
        "hints": [
            "Subtractive notation means a small letter before a big one: subtract twice and it cancels correctly.",
            "Compare current with NEXT, not previous.",
            "One left-to-right pass with a value lookup table suffices.",
        ],
        "python": """
class Solution:
    def romanToInt(self, s):
        val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        for i in range(len(s)):
            if i + 1 < len(s) and val[s[i]] < val[s[i + 1]]:
                total -= val[s[i]]
            else:
                total += val[s[i]]
        return total
""",
        "javascript": """
var romanToInt = function(s) {
    const val = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
    let total = 0;
    for (let i = 0; i < s.length; i++) {
        if (i + 1 < s.length && val[s[i]] < val[s[i + 1]]) total -= val[s[i]];
        else total += val[s[i]];
    }
    return total;
};
""",
        "java": """
class Solution {
    public int romanToInt(String s) {
        int[] val = new int[128];
        val['I'] = 1; val['V'] = 5; val['X'] = 10; val['L'] = 50;
        val['C'] = 100; val['D'] = 500; val['M'] = 1000;
        int total = 0;
        for (int i = 0; i < s.length(); i++) {
            if (i + 1 < s.length() && val[s.charAt(i)] < val[s.charAt(i + 1)]) total -= val[s.charAt(i)];
            else total += val[s.charAt(i)];
        }
        return total;
    }
}
""",
    },
}
