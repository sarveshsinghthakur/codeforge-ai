"""Real solutions + explanations for base problems (batch 2/4): edit-distance .. lowest-common-ancestor."""

SOLUTIONS = {
    "edit-distance": {
        "time": "O(m * n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. `dp[i][j]` is the edit distance between `word1[:i]` and `word2[:j]`.
2. If the last characters match, no operation is needed: `dp[i][j] = dp[i-1][j-1]`.
3. Otherwise take the best of three operations: insert (`dp[i][j-1]`), delete (`dp[i-1][j]`), replace (`dp[i-1][j-1]`) - each costs 1.
4. Base cases: converting to/from an empty string costs its full length.

Because each row only depends on the previous row, the table collapses to one array of size `n + 1`.""",
        "hints": [
            "dp[i][j] compares prefixes word1[:i] and word2[:j], not single characters.",
            "Matching last characters means 'do nothing' and diagonal movement.",
            "Three candidate operations - insert, delete, replace - each cost exactly 1.",
        ],
        "python": """
class Solution:
    def minDistance(self, word1, word2):
        m, n = len(word1), len(word2)
        prev = list(range(n + 1))
        for i in range(1, m + 1):
            cur = [i] + [0] * n
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    cur[j] = prev[j - 1]
                else:
                    cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])
            prev = cur
        return prev[n]
""",
        "javascript": """
var minDistance = function(word1, word2) {
    const m = word1.length, n = word2.length;
    let prev = Array.from({ length: n + 1 }, (_, j) => j);
    for (let i = 1; i <= m; i++) {
        const cur = new Array(n + 1).fill(0);
        cur[0] = i;
        for (let j = 1; j <= n; j++) {
            if (word1[i - 1] === word2[j - 1]) cur[j] = prev[j - 1];
            else cur[j] = 1 + Math.min(prev[j], cur[j - 1], prev[j - 1]);
        }
        prev = cur;
    }
    return prev[n];
};
""",
        "java": """
class Solution {
    public int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[] prev = new int[n + 1];
        for (int j = 0; j <= n; j++) prev[j] = j;
        for (int i = 1; i <= m; i++) {
            int[] cur = new int[n + 1];
            cur[0] = i;
            for (int j = 1; j <= n; j++) {
                if (word1.charAt(i - 1) == word2.charAt(j - 1)) cur[j] = prev[j - 1];
                else cur[j] = 1 + Math.min(prev[j], Math.min(cur[j - 1], prev[j - 1]));
            }
            prev = cur;
        }
        return prev[n];
    }
}
""",
    },
    "fibonacci-number": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. `F(0) = 0`, `F(1) = 1`, and `F(n) = F(n-1) + F(n-2)`.
2. Iterate from 2 up to `n`, rolling two variables forward each step.
3. Naive recursion is exponential because it recalculates the same subproblems; the iterative form visits each index once.

Constant memory, linear time.""",
        "hints": [
            "You only ever need the previous two values.",
            "Handle n = 0 and n = 1 before the loop.",
            "Memoized recursion works too, but iteration is simplest.",
        ],
        "python": """
class Solution:
    def fib(self, n):
        if n <= 1:
            return n
        prev2, prev1 = 0, 1
        for _ in range(2, n + 1):
            prev2, prev1 = prev1, prev1 + prev2
        return prev1
""",
        "javascript": """
var fib = function(n) {
    if (n <= 1) return n;
    let prev2 = 0, prev1 = 1;
    for (let i = 2; i <= n; i++) {
        const cur = prev1 + prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
};
""",
        "java": """
class Solution {
    public int fib(int n) {
        if (n <= 1) return n;
        int prev2 = 0, prev1 = 1;
        for (int i = 2; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""",
    },
    "find-maximum-in-array": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Assume the first element is the maximum.
2. Sweep the array; whenever a larger value appears, update the maximum.
3. Return the running maximum after the last element.

One pass over the array, constant extra space. For an empty array the problem constraints guarantee at least one element.""",
        "hints": [
            "Initialize the answer with the first element, not 0 (negatives!).",
            "A simple strict-greater comparison is all you need.",
            "Do not sort - it would cost O(n log n) for no benefit.",
        ],
        "python": """
class Solution:
    def findMax(self, nums):
        max_val = nums[0]
        for num in nums[1:]:
            if num > max_val:
                max_val = num
        return max_val
""",
        "javascript": """
var findMax = function(nums) {
    let max = nums[0];
    for (let i = 1; i < nums.length; i++) if (nums[i] > max) max = nums[i];
    return max;
};
""",
        "java": """
class Solution {
    public int findMax(int[] nums) {
        int max = nums[0];
        for (int i = 1; i < nums.length; i++) if (nums[i] > max) max = nums[i];
        return max;
    }
}
""",
    },
    "find-median-from-data-stream": {
        "time": "O(log n) add / O(1) findMedian",
        "space": "O(n)",
        "explanation": """**Approach**

1. Keep two heaps: a **max-heap** for the lower half and a **min-heap** for the upper half.
2. Insert each number into the max-heap first, then move its top into the min-heap - this guarantees every element of the lower half is <= every element of the upper half.
3. Rebalance so the max-heap holds either the same count or one more element than the min-heap.
4. If sizes are equal the median is the average of both tops; otherwise it is the max-heap top (the middle element).

Insertions are `O(log n)` through heap operations; reading the median touches only heap tops.""",
        "hints": [
            "Two heaps split the stream into a lower half and an upper half.",
            "Always rebalance after every insert so the size difference is at most 1.",
            "Careful with the even-count case: average the two tops as a float.",
        ],
        "python": """
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []
        self.hi = []

    def addNum(self, num):
        heapq.heappush(self.lo, -num)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2.0
""",
        "javascript": """
var MedianFinder = function() {
    this.data = [];
};

MedianFinder.prototype.addNum = function(num) {
    const arr = this.data;
    let lo = 0, hi = arr.length;
    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (arr[mid] < num) lo = mid + 1;
        else hi = mid;
    }
    arr.splice(lo, 0, num);
};

MedianFinder.prototype.findMedian = function() {
    const arr = this.data;
    const mid = arr.length >> 1;
    return arr.length % 2 ? arr[mid] : (arr[mid - 1] + arr[mid]) / 2;
};
""",
        "java": """
class MedianFinder {
    private PriorityQueue<Integer> lo = new PriorityQueue<>(Collections.reverseOrder());
    private PriorityQueue<Integer> hi = new PriorityQueue<>();

    public void addNum(int num) {
        lo.add(num);
        hi.add(lo.poll());
        if (hi.size() > lo.size()) lo.add(hi.poll());
    }

    public double findMedian() {
        if (lo.size() > hi.size()) return lo.peek();
        return (lo.peek() + hi.peek()) / 2.0;
    }
}
""",
    },
    "find-minimum-in-rotated-sorted-array": {
        "time": "O(log n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. The array is sorted but rotated; the minimum sits at the pivot where order breaks.
2. Binary search on `[lo, hi]`: compare `nums[mid]` with `nums[hi]`.
3. If `nums[mid] > nums[hi]` the pivot (minimum) is in the **right** half, so `lo = mid + 1`.
4. Otherwise the minimum is at `mid` or to its left, so `hi = mid`.

The loop maintains the invariant that the minimum always lies inside `[lo, hi]` and shrinks the range by half each step.""",
        "hints": [
            "Compare against the RIGHT boundary - it reveals which side the rotation pivot is on.",
            "nums[mid] <= nums[hi] means mid could itself be the minimum, so set hi = mid (not mid - 1).",
            "No duplicates here, so a plain binary search is enough.",
        ],
        "python": """
class Solution:
    def findMin(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1
            else:
                hi = mid
        return nums[lo]
""",
        "javascript": """
var findMin = function(nums) {
    let lo = 0, hi = nums.length - 1;
    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (nums[mid] > nums[hi]) lo = mid + 1;
        else hi = mid;
    }
    return nums[lo];
};
""",
        "java": """
class Solution {
    public int findMin(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] > nums[hi]) lo = mid + 1;
            else hi = mid;
        }
        return nums[lo];
    }
}
""",
    },
    "flatten-binary-tree-to-linked-list": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. The flattened list must follow preorder (root, left, right) with all `left` pointers set to `None`.
2. Iterative Morris-style pass: when a node has a left child, find the inorder predecessor (rightmost node of the left subtree).
3. Splice the original right subtree onto that predecessor's right, then move the left subtree to the right and clear `left`.
4. Advance to `node.right` and repeat.

Each edge of the tree is rewired at most twice, so the whole pass is linear with only pointer operations (no stack).""",
        "hints": [
            "The predecessor of a node in inorder is the rightmost node of its left subtree.",
            "Detach the old right subtree, attach it after the left subtree's tail, then move left to right.",
            "Always clear left pointers - the final list must be purely right-linked.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def flatten(self, root):
        cur = root
        while cur:
            if cur.left:
                pred = cur.left
                while pred.right:
                    pred = pred.right
                pred.right = cur.right
                cur.right = cur.left
                cur.left = None
            cur = cur.right
        return root
""",
        "javascript": """
var flatten = function(root) {
    let cur = root;
    while (cur) {
        if (cur.left) {
            let pred = cur.left;
            while (pred.right) pred = pred.right;
            pred.right = cur.right;
            cur.right = cur.left;
            cur.left = null;
        }
        cur = cur.right;
    }
    return root;
};
""",
        "java": """
class Solution {
    public TreeNode flatten(TreeNode root) {
        TreeNode cur = root;
        while (cur != null) {
            if (cur.left != null) {
                TreeNode pred = cur.left;
                while (pred.right != null) pred = pred.right;
                pred.right = cur.right;
                cur.right = cur.left;
                cur.left = null;
            }
            cur = cur.right;
        }
        return root;
    }
}
""",
    },
    "generate-parentheses": {
        "time": "O(4^n / sqrt(n))",
        "space": "O(n)",
        "explanation": """**Approach**

1. Build strings incrementally with two counters: `open` (how many `(` are placed) and `close`.
2. Add `(` whenever `open < n` - it never breaks validity.
3. Add `)` whenever `close < open` - closing more than we have opened would create an invalid prefix.
4. When the length reaches `2n`, a complete valid string is recorded.

The constraints keep the search tree small; each valid combination is produced exactly once in lexicographic-ish order.""",
        "hints": [
            "The pruning rule is close < open - never close what you have not opened.",
            "You may always add '(' up to n times.",
            "Think of it as building paths in a Catalan-number search tree.",
        ],
        "python": """
class Solution:
    def generateParenthesis(self, n):
        res = []

        def dfs(cur, open_, close):
            if len(cur) == 2 * n:
                res.append(cur)
                return
            if open_ < n:
                dfs(cur + '(', open_ + 1, close)
            if close < open_:
                dfs(cur + ')', open_, close + 1)

        dfs('', 0, 0)
        return res
""",
        "javascript": """
var generateParenthesis = function(n) {
    const res = [];
    const dfs = (cur, open, close) => {
        if (cur.length === 2 * n) { res.push(cur); return; }
        if (open < n) dfs(cur + '(', open + 1, close);
        if (close < open) dfs(cur + ')', open, close + 1);
    };
    dfs('', 0, 0);
    return res;
};
""",
        "java": """
class Solution {
    public List<String> generateParenthesis(int n) {
        List<String> res = new ArrayList<>();
        dfs("", 0, 0, n, res);
        return res;
    }
    private void dfs(String cur, int open, int close, int n, List<String> res) {
        if (cur.length() == 2 * n) { res.add(cur); return; }
        if (open < n) dfs(cur + "(", open + 1, close, n, res);
        if (close < open) dfs(cur + ")", open, close + 1, n, res);
    }
}
""",
    },
    "group-anagrams": {
        "time": "O(n * k log k)",
        "space": "O(n * k)",
        "explanation": """**Approach**

1. Two strings are anagrams iff their sorted character sequences are identical.
2. Use that sorted string as a hash key mapping to the list of original words.
3. Iterate once, bucketing each word under its key; finally return the bucket values.

`n` is the number of words and `k` the average word length; sorting each word costs `O(k log k)`.""",
        "hints": [
            "Sorting the characters gives a canonical signature for each anagram group.",
            "A hash map from signature -> list of words does all the grouping.",
            "Sorting each bucket before returning keeps output deterministic if tests compare order.",
        ],
        "python": """
class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for s in strs:
            key = ''.join(sorted(s))
            groups.setdefault(key, []).append(s)
        return list(groups.values())
""",
        "javascript": """
var groupAnagrams = function(strs) {
    const groups = {};
    for (const s of strs) {
        const key = s.split('').sort().join('');
        if (!groups[key]) groups[key] = [];
        groups[key].push(s);
    }
    return Object.values(groups);
};
""",
        "java": """
class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String s : strs) {
            char[] cs = s.toCharArray();
            Arrays.sort(cs);
            groups.computeIfAbsent(new String(cs), k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(groups.values());
    }
}
""",
    },
    "implement-trie": {
        "time": "O(L) per operation",
        "space": "O(total characters)",
        "explanation": """**Approach**

1. A trie node holds up to 26 children (one per letter) and an `is_word` flag marking the end of a stored word.
2. `insert` walks/creates nodes for each character and flags the final node.
3. `search` and `starts_with` both walk the chain; they differ only in the final check (word flag vs. merely reaching the node).
4. Every operation touches at most `L` nodes where `L` is the word length.

This makes prefix queries independent of how many words share the prefix.""",
        "hints": [
            "is_word on the last node distinguishes 'search' from 'starts_with'.",
            "Walk node by node; return False/None as soon as a child is missing.",
            "Store children in a dict if you prefer not to assume lowercase letters.",
        ],
        "python": """
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_word

    def startsWith(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
""",
        "javascript": """
var Trie = function() {
    this.root = {};
};

Trie.prototype.insert = function(word) {
    let node = this.root;
    for (const ch of word) {
        if (!node[ch]) node[ch] = {};
        node = node[ch];
    }
    node.isWord = true;
};

Trie.prototype.search = function(word) {
    let node = this.root;
    for (const ch of word) {
        if (!node[ch]) return false;
        node = node[ch];
    }
    return node.isWord === true;
};

Trie.prototype.startsWith = function(prefix) {
    let node = this.root;
    for (const ch of prefix) {
        if (!node[ch]) return false;
        node = node[ch];
    }
    return true;
};
""",
        "java": """
class Trie {
    private Trie[] children = new Trie[26];
    private boolean isWord = false;

    public void insert(String word) {
        Trie node = this;
        for (char ch : word.toCharArray()) {
            int i = ch - 'a';
            if (node.children[i] == null) node.children[i] = new Trie();
            node = node.children[i];
        }
        node.isWord = true;
    }

    public boolean search(String word) {
        Trie node = walk(word);
        return node != null && node.isWord;
    }

    public boolean startsWith(String prefix) {
        return walk(prefix) != null;
    }

    private Trie walk(String s) {
        Trie node = this;
        for (char ch : s.toCharArray()) {
            int i = ch - 'a';
            if (node.children[i] == null) return null;
            node = node.children[i];
        }
        return node;
    }
}
""",
    },
    "interval-list-intersections": {
        "time": "O(m + n)",
        "space": "O(m + n)",
        "explanation": """**Approach**

1. Two pointers `i` and `j` walk the two sorted interval lists.
2. The candidate intersection is `[max(start1, start2), min(end1, end2)]`; if start <= end it is a real overlap and gets recorded.
3. Advance the pointer whose current interval ends first - the other interval may still overlap the next one.
4. Stop when either list is exhausted.

Every interval is consumed once, giving a linear merge like merge-sort's merge step.""",
        "hints": [
            "Overlap exists only when max(starts) <= min(ends).",
            "Advance the interval with the SMALLER end; it can no longer intersect anything later.",
            "Both lists are already sorted - exploit that instead of hashing.",
        ],
        "python": """
class Solution:
    def intervalIntersection(self, firstList, secondList):
        i = j = 0
        res = []
        while i < len(firstList) and j < len(secondList):
            lo = max(firstList[i][0], secondList[j][0])
            hi = min(firstList[i][1], secondList[j][1])
            if lo <= hi:
                res.append([lo, hi])
            if firstList[i][1] < secondList[j][1]:
                i += 1
            else:
                j += 1
        return res
""",
        "javascript": """
var intervalIntersection = function(firstList, secondList) {
    let i = 0, j = 0;
    const res = [];
    while (i < firstList.length && j < secondList.length) {
        const lo = Math.max(firstList[i][0], secondList[j][0]);
        const hi = Math.min(firstList[i][1], secondList[j][1]);
        if (lo <= hi) res.push([lo, hi]);
        if (firstList[i][1] < secondList[j][1]) i++;
        else j++;
    }
    return res;
};
""",
        "java": """
class Solution {
    public int[][] intervalIntersection(int[][] firstList, int[][] secondList) {
        int i = 0, j = 0;
        List<int[]> res = new ArrayList<>();
        while (i < firstList.length && j < secondList.length) {
            int lo = Math.max(firstList[i][0], secondList[j][0]);
            int hi = Math.min(firstList[i][1], secondList[j][1]);
            if (lo <= hi) res.add(new int[]{lo, hi});
            if (firstList[i][1] < secondList[j][1]) i++;
            else j++;
        }
        return res.toArray(new int[0][]);
    }
}
""",
    },
    "jump-game": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Track `reach`, the furthest index you can currently get to.
2. Scan left to right: if the current index is beyond `reach`, you are stuck - return `False`.
3. Otherwise update `reach = max(reach, i + nums[i])`.
4. If the scan finishes, `reach >= n - 1`, so the last index is reachable.

You never need to decide WHERE to jump - only whether any jump could get you there.""",
        "hints": [
            "Greedy: keep the maximum reachable index instead of trying every path.",
            "You cannot even REACH index i if i > reach.",
            "Early exit the moment an unreachable index appears.",
        ],
        "python": """
class Solution:
    def canJump(self, nums):
        reach = 0
        for i, step in enumerate(nums):
            if i > reach:
                return False
            reach = max(reach, i + step)
            if reach >= len(nums) - 1:
                return True
        return True
""",
        "javascript": """
var canJump = function(nums) {
    let reach = 0;
    for (let i = 0; i < nums.length; i++) {
        if (i > reach) return false;
        reach = Math.max(reach, i + nums[i]);
        if (reach >= nums.length - 1) return true;
    }
    return true;
};
""",
        "java": """
class Solution {
    public boolean canJump(int[] nums) {
        int reach = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > reach) return false;
            reach = Math.max(reach, i + nums[i]);
            if (reach >= nums.length - 1) return true;
        }
        return true;
    }
}
""",
    },
    "kth-largest-element-in-an-array": {
        "time": "O(n) average",
        "space": "O(1)",
        "explanation": """**Approach**

1. The k-th largest is the element at index `k - 1` in descending order, i.e. at index `n - k` in ascending order.
2. Use quickselect: pick a pivot, partition the array so smaller values are left and larger values are right.
3. Recurse only into the side that contains index `n - k`; each partition halves the search space on average.
4. The average cost is `n + n/2 + n/4 + ... = O(n)`; a randomized pivot keeps the worst case rare.

(An `O(n log n)` sort also passes, but quickselect avoids sorting everything.)""",
        "hints": [
            "k-th LARGEST == index n - k when sorted ascending.",
            "Partition once and only recurse into the half containing your target index.",
            "A randomized pivot protects against already-sorted inputs.",
        ],
        "python": """
class Solution:
    def findKthLargest(self, nums, k):
        target = len(nums) - k

        def select(lo, hi):
            pivot = nums[hi]
            i = lo
            for j in range(lo, hi):
                if nums[j] <= pivot:
                    nums[i], nums[j] = nums[j], nums[i]
                    i += 1
            nums[i], nums[hi] = nums[hi], nums[i]
            if i == target:
                return nums[i]
            if i < target:
                return select(i + 1, hi)
            return select(lo, i - 1)

        return select(0, len(nums) - 1)
""",
        "javascript": """
var findKthLargest = function(nums, k) {
    const target = nums.length - k;
    const select = (lo, hi) => {
        const pivot = nums[hi];
        let i = lo;
        for (let j = lo; j < hi; j++) {
            if (nums[j] <= pivot) {
                [nums[i], nums[j]] = [nums[j], nums[i]];
                i++;
            }
        }
        [nums[i], nums[hi]] = [nums[hi], nums[i]];
        if (i === target) return nums[i];
        if (i < target) return select(i + 1, hi);
        return select(lo, i - 1);
    };
    return select(0, nums.length - 1);
};
""",
        "java": """
class Solution {
    public int findKthLargest(int[] nums, int k) {
        int target = nums.length - k;
        return select(nums, 0, nums.length - 1, target);
    }
    private int select(int[] nums, int lo, int hi, int target) {
        int pivot = nums[hi], i = lo;
        for (int j = lo; j < hi; j++) {
            if (nums[j] <= pivot) {
                int t = nums[i]; nums[i] = nums[j]; nums[j] = t;
                i++;
            }
        }
        int t = nums[i]; nums[i] = nums[hi]; nums[hi] = t;
        if (i == target) return nums[i];
        if (i < target) return select(nums, i + 1, hi, target);
        return select(nums, lo, i - 1, target);
    }
}
""",
    },
    "length-of-last-word": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Skip any trailing spaces from the end of the string.
2. Walk backwards until a space (or the start of the string) is hit, counting characters.
3. The count is the length of the last word.

A single reverse scan avoids splitting the whole string and uses constant extra memory.""",
        "hints": [
            "Start from the end - leading spaces in the middle never matter.",
            "Trim trailing spaces first, otherwise your count starts at 0.",
            "Stop counting at the first space you encounter.",
        ],
        "python": """
class Solution:
    def lengthOfLastWord(self, s):
        i = len(s) - 1
        while i >= 0 and s[i] == ' ':
            i -= 1
        count = 0
        while i >= 0 and s[i] != ' ':
            count += 1
            i -= 1
        return count
""",
        "javascript": """
var lengthOfLastWord = function(s) {
    let i = s.length - 1;
    while (i >= 0 && s[i] === ' ') i--;
    let count = 0;
    while (i >= 0 && s[i] !== ' ') { count++; i--; }
    return count;
};
""",
        "java": """
class Solution {
    public int lengthOfLastWord(String s) {
        int i = s.length() - 1;
        while (i >= 0 && s.charAt(i) == ' ') i--;
        int count = 0;
        while (i >= 0 && s.charAt(i) != ' ') { count++; i--; }
        return count;
    }
}
""",
    },
    "letter-combinations-of-a-phone-number": {
        "time": "O(3^m * 4^n)",
        "space": "O(m + n)",
        "explanation": """**Approach**

1. Map each digit to its keypad letters (2 -> abc, 7 -> pqrs, etc.).
2. Backtrack over the digits: at position `i`, append every letter of `digits[i]` and recurse to `i + 1`.
3. When the built string's length equals the digit count, record it.
4. An empty input produces no combinations (return `[]`).

The search tree has `3^m * 4^n` leaves where `m`/`n` count the 3-letter and 4-letter keys.""",
        "hints": [
            "Empty digits means zero combinations - guard the base case.",
            "Keep a mapping dict from digit to letters.",
            "Build one string per branch and pop it when backtracking (or pass a copy).",
        ],
        "python": """
class Solution:
    def letterCombinations(self, digits):
        if digits is None:
            return []
        digits = str(digits)
        if not digits:
            return []
        pad = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
               '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
        res = []

        def dfs(idx, cur):
            if idx == len(digits):
                res.append(cur)
                return
            for ch in pad[digits[idx]]:
                dfs(idx + 1, cur + ch)

        dfs(0, '')
        return res
""",
        "javascript": """
var letterCombinations = function(digits) {
    if (digits === null || digits === undefined) return [];
    digits = String(digits);
    if (!digits) return [];
    const pad = { '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
                  '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz' };
    const res = [];
    const dfs = (idx, cur) => {
        if (idx === digits.length) { res.push(cur); return; }
        for (const ch of pad[digits[idx]]) dfs(idx + 1, cur + ch);
    };
    dfs(0, '');
    return res;
};
""",
        "java": """
class Solution {
    private static final String[] PAD = {"", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};
    public List<String> letterCombinations(String digits) {
        List<String> res = new ArrayList<>();
        if (digits == null || digits.isEmpty()) return res;
        dfs(digits, 0, new StringBuilder(), res);
        return res;
    }
    private void dfs(String d, int idx, StringBuilder cur, List<String> res) {
        if (idx == d.length()) { res.add(cur.toString()); return; }
        String letters = PAD[d.charAt(idx) - '0'];
        for (int i = 0; i < letters.length(); i++) {
            cur.append(letters.charAt(i));
            dfs(d, idx + 1, cur, res);
            cur.deleteCharAt(cur.length() - 1);
        }
    }
}
""",
    },
    "linked-list-cycle": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Floyd's tortoise-and-hare algorithm: move a slow pointer one step and a fast pointer two steps.
2. If a cycle exists, the fast pointer laps the slow pointer inside the cycle and they become equal.
3. If the fast pointer reaches the end (`None`), there is no cycle.

Both pointers stay on the list itself, so no hash set of visited nodes (and its `O(n)` memory) is required.""",
        "hints": [
            "Two pointers at different speeds must meet if - and only if - a cycle exists.",
            "Check for the end BEFORE moving the fast pointer.",
            "A visited-set solution works but uses O(n) memory; the interview follow-up usually bans it.",
        ],
        "python": """
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution:
    def hasCycle(self, head, pos=None):
        if head is None:
            return False
        if pos is not None:
            nodes = []
            cur = head
            seen = set()
            while cur is not None and id(cur) not in seen:
                seen.add(id(cur))
                nodes.append(cur)
                cur = cur.next
            if cur is None and 0 <= pos < len(nodes):
                nodes[-1].next = nodes[pos]
        slow = head
        fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False
""",
        "javascript": """
var hasCycle = function(head, pos) {
    if (!head) return false;
    if (pos !== null && pos !== undefined) {
        const nodes = [];
        const seen = new Set();
        let cur = head;
        while (cur !== null && !seen.has(cur)) {
            seen.add(cur);
            nodes.push(cur);
            cur = cur.next;
        }
        if (cur === null && pos >= 0 && pos < nodes.length) {
            nodes[nodes.length - 1].next = nodes[pos];
        }
    }
    let slow = head, fast = head;
    while (fast && fast.next) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow === fast) return true;
    }
    return false;
};
""",
        "java": """
class Solution {
    public boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }
}
""",
    },
    "longest-consecutive-sequence": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Put every number into a set for `O(1)` lookups.
2. Only start counting when `num - 1` is **not** in the set - that means `num` is the start of a fresh sequence.
3. Walk forward (`num + 1`, `num + 2`, ...) counting the run length and keep the maximum.
4. Each element joins at most one sequence, so despite the inner while-loop the total work is linear.""",
        "hints": [
            "Only begin a streak from a number that has no predecessor in the set.",
            "This trick keeps the whole algorithm O(n) - each element is visited once.",
            "Duplicates are harmless because the set removes them.",
        ],
        "python": """
class Solution:
    def longestConsecutive(self, nums):
        seen = set(nums)
        best = 0
        for num in seen:
            if num - 1 in seen:
                continue
            length = 1
            while num + length in seen:
                length += 1
            if length > best:
                best = length
        return best
""",
        "javascript": """
var longestConsecutive = function(nums) {
    const seen = new Set(nums);
    let best = 0;
    for (const num of seen) {
        if (seen.has(num - 1)) continue;
        let length = 1;
        while (seen.has(num + length)) length++;
        if (length > best) best = length;
    }
    return best;
};
""",
        "java": """
class Solution {
    public int longestConsecutive(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int n : nums) seen.add(n);
        int best = 0;
        for (int num : seen) {
            if (seen.contains(num - 1)) continue;
            int length = 1;
            while (seen.contains(num + length)) length++;
            best = Math.max(best, length);
        }
        return best;
    }
}
""",
    },
    "longest-increasing-subsequence": {
        "time": "O(n log n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Maintain `tails`, where `tails[i]` is the smallest possible tail of an increasing subsequence of length `i + 1`.
2. For each number, binary-search its position in `tails`:
   - If it is larger than everything, append (extends the longest subsequence).
   - Otherwise replace the first element `>= num` - this keeps tails as small as possible without changing any length.
3. The length of `tails` at the end is the LIS length (the actual subsequence can be recovered with parent pointers).

Each element costs one `O(log n)` binary search.""",
        "hints": [
            "tails is NOT the LIS itself - only its length is guaranteed correct.",
            "Replacing the first tail >= num keeps future extensions viable.",
            "Use bisect_left so duplicates of the same value do not inflate the length.",
        ],
        "python": """
class Solution:
    def lengthOfLIS(self, nums):
        import bisect
        tails = []
        for n in nums:
            i = bisect.bisect_left(tails, n)
            if i == len(tails):
                tails.append(n)
            else:
                tails[i] = n
        return len(tails)
""",
        "javascript": """
var lengthOfLIS = function(nums) {
    const tails = [];
    for (const n of nums) {
        let lo = 0, hi = tails.length;
        while (lo < hi) {
            const mid = (lo + hi) >> 1;
            if (tails[mid] < n) lo = mid + 1;
            else hi = mid;
        }
        if (lo === tails.length) tails.push(n);
        else tails[lo] = n;
    }
    return tails.length;
};
""",
        "java": """
class Solution {
    public int lengthOfLIS(int[] nums) {
        int[] tails = new int[nums.length];
        int size = 0;
        for (int n : nums) {
            int lo = 0, hi = size;
            while (lo < hi) {
                int mid = lo + (hi - lo) / 2;
                if (tails[mid] < n) lo = mid + 1;
                else hi = mid;
            }
            tails[lo] = n;
            if (lo == size) size++;
        }
        return size;
    }
}
""",
    },
    "longest-substring-without-repeating-characters": {
        "time": "O(n)",
        "space": "O(min(n, alphabet))",
        "explanation": """**Approach**

1. Slide a window `[left, right]` over the string while remembering the last index of every character seen.
2. When `s[right]` was already seen at an index `>= left`, jump `left` to `last[s[right]] + 1` so the window is duplicate-free again.
3. After adjusting, the window length `right - left + 1` is a candidate answer.
4. Update the character's last-seen index to `right`.

Each pointer moves forward at most `n` times, so the scan is linear.""",
        "hints": [
            "Store the LAST index of each character, not just a boolean.",
            "Only move left forward - never backward (that would break linearity).",
            "The new left is max(left, lastSeen + 1) so you never rewind past the current window.",
        ],
        "python": """
class Solution:
    def lengthOfLongestSubstring(self, s):
        last = {}
        left = 0
        best = 0
        for right, ch in enumerate(s):
            if ch in last and last[ch] >= left:
                left = last[ch] + 1
            last[ch] = right
            best = max(best, right - left + 1)
        return best
""",
        "javascript": """
var lengthOfLongestSubstring = function(s) {
    const last = new Map();
    let left = 0, best = 0;
    for (let right = 0; right < s.length; right++) {
        const ch = s[right];
        if (last.has(ch) && last.get(ch) >= left) left = last.get(ch) + 1;
        last.set(ch, right);
        best = Math.max(best, right - left + 1);
    }
    return best;
};
""",
        "java": """
class Solution {
    public int lengthOfLongestSubstring(String s) {
        Map<Character, Integer> last = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char ch = s.charAt(right);
            if (last.containsKey(ch) && last.get(ch) >= left) left = last.get(ch) + 1;
            last.put(ch, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
""",
    },
    "longest-valid-parentheses": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Scan with a stack seeded with `-1` as a sentinel marking the start of the current valid segment.
2. On `(` push its index; on `)` pop. If the stack becomes empty after popping, push the current index as the new sentinel.
3. Otherwise the segment length is `current index - stack top`, which is the length of the valid run ending here.
4. Track the maximum of those lengths.

The stack guarantees you always measure from the last unmatched `(` (or sentinel).""",
        "hints": [
            "Seed the stack with -1 so a fully matched run still has a baseline index.",
            "After popping, an EMPTY stack means you just closed the last unmatched '(' - use the current index as the new base.",
            "A single-pass stack solution beats the naive O(n^2) check-every-substring approach.",
        ],
        "python": """
class Solution:
    def longestValidParentheses(self, s):
        stack = [-1]
        best = 0
        for i, ch in enumerate(s):
            if ch == '(':
                stack.append(i)
            else:
                stack.pop()
                if not stack:
                    stack.append(i)
                else:
                    best = max(best, i - stack[-1])
        return best
""",
        "javascript": """
var longestValidParentheses = function(s) {
    const stack = [-1];
    let best = 0;
    for (let i = 0; i < s.length; i++) {
        if (s[i] === '(') stack.push(i);
        else {
            stack.pop();
            if (stack.length === 0) stack.push(i);
            else best = Math.max(best, i - stack[stack.length - 1]);
        }
    }
    return best;
};
""",
        "java": """
class Solution {
    public int longestValidParentheses(String s) {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(-1);
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '(') stack.push(i);
            else {
                stack.pop();
                if (stack.isEmpty()) stack.push(i);
                else best = Math.max(best, i - stack.peek());
            }
        }
        return best;
    }
}
""",
    },
    "lowest-common-ancestor-of-a-binary-tree": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. Post-order recursion: process the left subtree, then the right, then decide for the current node.
2. If the current node itself is `p` or `q`, it is the answer (one node may be an ancestor of the other).
3. Otherwise look at the recursive results: if **both** sides return a node, the current node is the split point (LCA); if only one side returns a node, bubble it up.
4. A `None` result means neither target lives in that subtree.

Each node is visited once; the recursion depth is the tree height.""",
        "hints": [
            "Found a target? Return it immediately - it becomes the answer for your parent.",
            "Both children returning non-null means THIS node is the LCA.",
            "Only one side non-null? Pass that result upward unchanged.",
        ],
        "python": """
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
        "javascript": """
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
        "java": """
class Solution {
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;
        TreeNode left = lowestCommonAncestor(root.left, p, q);
        TreeNode right = lowestCommonAncestor(root.right, p, q);
        if (left != null && right != null) return root;
        return left != null ? left : right;
    }
}
""",
    },
}
