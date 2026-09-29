"""Real solutions + explanations for base problems (batch 1/4): 3sum .. decode-ways."""

SOLUTIONS = {
    "3sum": {
        "time": "O(n^2)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Sort the array first so duplicates become adjacent and the two-pointer scan works.
2. Fix one index `i` as the first number, then search the range `(i+1, n-1)` for a pair that sums to `-nums[i]`.
3. Move the left pointer right on a too-small sum, move the right pointer left on a too-large sum.
4. Skip duplicate values for both `i` and the inner pair so each unique triplet is emitted exactly once.

The sort costs `O(n log n)` and each fixed `i` costs `O(n)`, giving `O(n^2)` overall. The two-pointer step never needs a hash set, which keeps extra space constant.""",
        "hints": [
            "Sorting the input first makes duplicate handling and two-pointer movement possible.",
            "For each index i, treat the remaining problem as a classic two-sum on nums[i+1:] with target -nums[i].",
            "Always advance i past duplicate values, otherwise you will report the same triplet repeatedly.",
        ],
        "python": """
class Solution:
    def threeSum(self, nums):
        nums.sort()
        n = len(nums)
        res = []
        for i in range(n - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            if nums[i] > 0:
                break
            lo, hi = i + 1, n - 1
            target = -nums[i]
            while lo < hi:
                s = nums[lo] + nums[hi]
                if s < target:
                    lo += 1
                elif s > target:
                    hi -= 1
                else:
                    res.append([nums[i], nums[lo], nums[hi]])
                    lo += 1
                    hi -= 1
                    while lo < hi and nums[lo] == nums[lo - 1]:
                        lo += 1
                    while lo < hi and nums[hi] == nums[hi + 1]:
                        hi -= 1
        return res
""",
        "javascript": """
var threeSum = function(nums) {
    nums.sort((a, b) => a - b);
    const res = [];
    const n = nums.length;
    for (let i = 0; i < n - 2; i++) {
        if (i > 0 && nums[i] === nums[i - 1]) continue;
        if (nums[i] > 0) break;
        let lo = i + 1, hi = n - 1;
        const target = -nums[i];
        while (lo < hi) {
            const s = nums[lo] + nums[hi];
            if (s < target) lo++;
            else if (s > target) hi--;
            else {
                res.push([nums[i], nums[lo], nums[hi]]);
                lo++; hi--;
                while (lo < hi && nums[lo] === nums[lo - 1]) lo++;
                while (lo < hi && nums[hi] === nums[hi + 1]) hi--;
            }
        }
    }
    return res;
};
""",
        "java": """
class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> res = new ArrayList<>();
        int n = nums.length;
        for (int i = 0; i < n - 2; i++) {
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            if (nums[i] > 0) break;
            int lo = i + 1, hi = n - 1, target = -nums[i];
            while (lo < hi) {
                int s = nums[lo] + nums[hi];
                if (s < target) lo++;
                else if (s > target) hi--;
                else {
                    res.add(Arrays.asList(nums[i], nums[lo], nums[hi]));
                    lo++; hi--;
                    while (lo < hi && nums[lo] == nums[lo - 1]) lo++;
                    while (lo < hi && nums[hi] == nums[hi + 1]) hi--;
                }
            }
        }
        return res;
    }
}
""",
    },
    "add-binary": {
        "time": "O(max(len(a), len(b)))",
        "space": "O(max(len(a), len(b)))",
        "explanation": """**Approach**

1. Walk both strings from the least significant digit (the end) toward the most significant digit.
2. At every step add the two digits plus the carry; the new digit is `sum % 2` and the new carry is `sum // 2`.
3. When one string is exhausted its digits count as `0`; keep going until both strings and the carry are consumed.
4. Reverse the collected digits to form the result.

This is exactly grade-school addition in base 2 and runs in a single linear pass.""",
        "hints": [
            "Process digits from right to left so you always know the place value you are adding.",
            "Keep an integer carry (0 or 1) instead of juggling strings.",
            "Do not forget the final carry after the loop ends.",
        ],
        "python": """
class Solution:
    def addBinary(self, a, b):
        if not isinstance(a, str):
            a = str(int(a))
        if not isinstance(b, str):
            b = str(int(b))
        i, j = len(a) - 1, len(b) - 1
        carry = 0
        out = []
        while i >= 0 or j >= 0 or carry:
            da = ord(a[i]) - 48 if i >= 0 else 0
            db = ord(b[j]) - 48 if j >= 0 else 0
            total = da + db + carry
            out.append(chr(total % 2 + 48))
            carry = total // 2
            i -= 1
            j -= 1
        return ''.join(reversed(out))
""",
        "javascript": """
var addBinary = function(a, b) {
    if (typeof a !== 'string') a = String(a);
    if (typeof b !== 'string') b = String(b);
    let i = a.length - 1, j = b.length - 1, carry = 0;
    let out = '';
    while (i >= 0 || j >= 0 || carry) {
        const da = i >= 0 ? a.charCodeAt(i) - 48 : 0;
        const db = j >= 0 ? b.charCodeAt(j) - 48 : 0;
        const total = da + db + carry;
        out = String.fromCharCode((total % 2) + 48) + out;
        carry = total >> 1;
        i--; j--;
    }
    return out;
};
""",
        "java": """
class Solution {
    public String addBinary(String a, String b) {
        StringBuilder sb = new StringBuilder();
        int i = a.length() - 1, j = b.length() - 1, carry = 0;
        while (i >= 0 || j >= 0 || carry > 0) {
            int da = i >= 0 ? a.charAt(i) - '0' : 0;
            int db = j >= 0 ? b.charAt(j) - '0' : 0;
            int total = da + db + carry;
            sb.append(total % 2);
            carry = total / 2;
            i--; j--;
        }
        return sb.reverse().toString();
    }
}
""",
    },
    "add-two-numbers": {
        "time": "O(max(m, n))",
        "space": "O(max(m, n))",
        "explanation": """**Approach**

1. Create a dummy head node so appending to the result list is uniform and you never special-case the first node.
2. Traverse `l1` and `l2` in lockstep, adding both values plus the carry.
3. Each new node stores `total % 10`, and the carry becomes `total // 10`.
4. When one list runs out, continue with the other; finally attach any leftover carry.

The result length is at most `max(m, n) + 1` and every node is visited once.""",
        "hints": [
            "A dummy head node removes all 'is this the first node?' branching.",
            "Carry can be at most 1 because the maximum digit sum is 9 + 9 + 1 = 19.",
            "One list may be longer - keep looping while either list or the carry remains.",
        ],
        "python": """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        dummy = ListNode(0)
        tail = dummy
        carry = 0
        while l1 or l2 or carry:
            v1 = l1.val if l1 else 0
            v2 = l2.val if l2 else 0
            total = v1 + v2 + carry
            carry = total // 10
            tail.next = ListNode(total % 10)
            tail = tail.next
            if l1:
                l1 = l1.next
            if l2:
                l2 = l2.next
        return dummy.next
""",
        "javascript": """
var addTwoNumbers = function(l1, l2) {
    const dummy = new ListNode(0);
    let tail = dummy;
    let carry = 0;
    while (l1 || l2 || carry) {
        const v1 = l1 ? l1.val : 0;
        const v2 = l2 ? l2.val : 0;
        const total = v1 + v2 + carry;
        carry = Math.floor(total / 10);
        tail.next = new ListNode(total % 10);
        tail = tail.next;
        if (l1) l1 = l1.next;
        if (l2) l2 = l2.next;
    }
    return dummy.next;
};
""",
        "java": """
class Solution {
    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry > 0) {
            int v1 = l1 != null ? l1.val : 0;
            int v2 = l2 != null ? l2.val : 0;
            int total = v1 + v2 + carry;
            carry = total / 10;
            tail.next = new ListNode(total % 10);
            tail = tail.next;
            if (l1 != null) l1 = l1.next;
            if (l2 != null) l2 = l2.next;
        }
        return dummy.next;
    }
}
""",
    },
    "alien-dictionary": {
        "time": "O(C + U)",
        "space": "O(U^2)",
        "explanation": """**Approach**

1. Every unique character is a node. Characters that never appear in any comparison must still be included.
2. Compare each adjacent pair of words: the first differing character gives a directed edge `prev -> next` (prev sorts earlier).
3. If a pair has the form `word1` being a strict prefix of `word2` (`abc` before `ab`), the ordering is impossible - return `""`.
4. Run topological sort (Kahn's algorithm) on the graph. If a cycle exists, no valid order exists.

`C` is the total number of characters across all words, `U` the number of unique letters.""",
        "hints": [
            "The edge direction comes from the FIRST character that differs between adjacent words.",
            "A longer word appearing before its own prefix is a contradiction.",
            "Use indegrees + a queue (Kahn) and detect cycles by checking that all nodes were emitted.",
        ],
        "python": """
class Solution:
    def alienOrder(self, words):
        adj = {c: set() for w in words for c in w}
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i + 1]
            if len(w1) > len(w2) and w1.startswith(w2):
                return ""
            for a, b in zip(w1, w2):
                if a != b:
                    adj[a].add(b)
                    break
        indeg = {c: 0 for c in adj}
        for nxts in adj.values():
            for n in nxts:
                indeg[n] += 1
        queue = [c for c in indeg if indeg[c] == 0]
        order = []
        while queue:
            c = queue.pop()
            order.append(c)
            for n in adj[c]:
                indeg[n] -= 1
                if indeg[n] == 0:
                    queue.append(n)
        if len(order) != len(adj):
            return ""
        return ''.join(order)
""",
        "javascript": """
var alienOrder = function(words) {
    const adj = {};
    for (const w of words) for (const c of w) if (!adj[c]) adj[c] = new Set();
    for (let i = 0; i < words.length - 1; i++) {
        const w1 = words[i], w2 = words[i + 1];
        if (w1.length > w2.length && w1.startsWith(w2)) return '';
        for (let k = 0; k < Math.min(w1.length, w2.length); k++) {
            if (w1[k] !== w2[k]) { adj[w1[k]].add(w2[k]); break; }
        }
    }
    const indeg = {};
    for (const c in adj) indeg[c] = 0;
    for (const c in adj) for (const n of adj[c]) indeg[n]++;
    const queue = Object.keys(indeg).filter(c => indeg[c] === 0);
    let order = '';
    while (queue.length) {
        const c = queue.shift();
        order += c;
        for (const n of adj[c]) if (--indeg[n] === 0) queue.push(n);
    }
    return order.length === Object.keys(adj).length ? order : '';
};
""",
        "java": """
class Solution {
    public String alienOrder(String[] words) {
        Map<Character, Set<Character>> adj = new HashMap<>();
        for (String w : words) for (char c : w) adj.putIfAbsent(c, new HashSet<>());
        for (int i = 0; i < words.length - 1; i++) {
            String w1 = words[i], w2 = words[i + 1];
            if (w1.length() > w2.length() && w1.startsWith(w2)) return "";
            int k = 0;
            while (k < w1.length() && k < w2.length() && w1.charAt(k) == w2.charAt(k)) k++;
            if (k < w1.length() && k < w2.length()) adj.get(w1.charAt(k)).add(w2.charAt(k));
        }
        Map<Character, Integer> indeg = new HashMap<>();
        for (char c : adj.keySet()) indeg.put(c, 0);
        for (char c : adj.keySet()) for (char n : adj.get(c)) indeg.put(n, indeg.get(n) + 1);
        Queue<Character> q = new LinkedList<>();
        for (char c : indeg.keySet()) if (indeg.get(c) == 0) q.add(c);
        StringBuilder sb = new StringBuilder();
        while (!q.isEmpty()) {
            char c = q.poll();
            sb.append(c);
            for (char n : adj.get(c)) if (indeg.merge(n, -1, Integer::sum) == 0) q.add(n);
        }
        return sb.length() == adj.size() ? sb.toString() : "";
    }
}
""",
    },
    "best-time-to-buy-and-sell-stock": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Track the lowest price seen so far while scanning left to right.
2. At each day compute the profit you would earn by selling today: `price - min_so_far`.
3. Keep the maximum of those profits.
4. Because the buy must happen before the sell, a single pass with running minimum is sufficient.

One pass, constant memory, and no need to store all prices.""",
        "hints": [
            "You only need the cheapest price encountered BEFORE the current day.",
            "Update the minimum and the maximum profit in the same iteration.",
            "If prices only fall, the answer is 0 (never trade).",
        ],
        "python": """
class Solution:
    def maxProfit(self, prices):
        min_price = float('inf')
        best = 0
        for p in prices:
            if p < min_price:
                min_price = p
            else:
                best = max(best, p - min_price)
        return best
""",
        "javascript": """
var maxProfit = function(prices) {
    let minPrice = Infinity, best = 0;
    for (const p of prices) {
        if (p < minPrice) minPrice = p;
        else best = Math.max(best, p - minPrice);
    }
    return best;
};
""",
        "java": """
class Solution {
    public int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE, best = 0;
        for (int p : prices) {
            if (p < minPrice) minPrice = p;
            else best = Math.max(best, p - minPrice);
        }
        return best;
    }
}
""",
    },
    "binary-tree-inorder-traversal": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. Inorder traversal visits nodes in the order **left -> root -> right**, which yields sorted values on a BST.
2. Iterative version: push the left spine onto a stack, then pop a node, record its value, and repeat on its right child.
3. The stack holds at most the height `h` of the tree, so extra space is `O(h)` (worst `O(n)` for a skewed tree).
4. Every node is pushed and popped exactly once, giving a linear pass.""",
        "hints": [
            "Keep moving to the left child until you hit null - that is exactly when you are ready to visit a node.",
            "After visiting a node, switch to its right subtree.",
            "Recursion is fine too, but the stack version shows the O(h) space bound clearly.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def inorderTraversal(self, root):
        res = []
        stack = []
        cur = root
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            res.append(cur.val)
            cur = cur.right
        return res
""",
        "javascript": """
var inorderTraversal = function(root) {
    const res = [];
    const stack = [];
    let cur = root;
    while (cur || stack.length) {
        while (cur) {
            stack.push(cur);
            cur = cur.left;
        }
        cur = stack.pop();
        res.push(cur.val);
        cur = cur.right;
    }
    return res;
};
""",
        "java": """
class Solution {
    public List<Integer> inorderTraversal(TreeNode root) {
        List<Integer> res = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {
                stack.push(cur);
                cur = cur.left;
            }
            cur = stack.pop();
            res.add(cur.val);
            cur = cur.right;
        }
        return res;
    }
}
""",
    },
    "binary-tree-level-order-traversal": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Breadth-first search with a queue: start with the root in the queue.
2. For each level, take a snapshot of the queue size - that count is exactly how many nodes belong to the current level.
3. Pop that many nodes, record their values into a level list, and enqueue their children for the next level.
4. Repeat until the queue is empty.

Each node is enqueued once, so time is `O(n)`; the queue holds up to one full level (worst `O(n)`).""",
        "hints": [
            "Capture queue.length BEFORE processing a level - it changes as you enqueue children.",
            "One queue is enough; you do not need a separate queue per level.",
            "An empty tree should return an empty list, not [[]].",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def levelOrder(self, root):
        if not root:
            return []
        res = []
        queue = [root]
        while queue:
            level = []
            for _ in range(len(queue)):
                node = queue.pop(0)
                level.append(node.val)
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
            res.append(level)
        return res
""",
        "javascript": """
var levelOrder = function(root) {
    if (!root) return [];
    const res = [];
    const queue = [root];
    while (queue.length) {
        const level = [];
        const size = queue.length;
        for (let i = 0; i < size; i++) {
            const node = queue.shift();
            level.push(node.val);
            if (node.left) queue.push(node.left);
            if (node.right) queue.push(node.right);
        }
        res.push(level);
    }
    return res;
};
""",
        "java": """
class Solution {
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> res = new ArrayList<>();
        if (root == null) return res;
        Queue<TreeNode> queue = new LinkedList<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.add(node.left);
                if (node.right != null) queue.add(node.right);
            }
            res.add(level);
        }
        return res;
    }
}
""",
    },
    "binary-tree-maximum-path-sum": {
        "time": "O(n)",
        "space": "O(h)",
        "explanation": """**Approach**

1. A path may bend at most once, so think of every node as a potential **highest point** of the path.
2. Define `gain(node) = node.val + max(0, gain(left), gain(right))`: the best downward chain starting at `node`.
3. While computing the gain, the best path **through** `node` is `node.val + max(0, gain(left)) + max(0, gain(right))`.
4. Keep a global maximum over all nodes; negative children contribute 0 because we can simply not extend through them.

One post-order DFS visits each node once.""",
        "hints": [
            "A node contributes a negative subtree only if you are forced to - you can always cut it off with max(0, ...).",
            "Two different values matter: the best CHAIN you can return upward, and the best PATH that bends at this node.",
            "Initialize the global best to negative infinity; all values may be negative.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def maxPathSum(self, root):
        best = [float('-inf')]

        def gain(node):
            if not node:
                return 0
            left = max(0, gain(node.left))
            right = max(0, gain(node.right))
            best[0] = max(best[0], node.val + left + right)
            return node.val + max(left, right)

        gain(root)
        return best[0]
""",
        "javascript": """
var maxPathSum = function(root) {
    let best = -Infinity;
    const gain = (node) => {
        if (!node) return 0;
        const left = Math.max(0, gain(node.left));
        const right = Math.max(0, gain(node.right));
        best = Math.max(best, node.val + left + right);
        return node.val + Math.max(left, right);
    };
    gain(root);
    return best;
};
""",
        "java": """
class Solution {
    int best = Integer.MIN_VALUE;
    public int maxPathSum(TreeNode root) {
        gain(root);
        return best;
    }
    private int gain(TreeNode node) {
        if (node == null) return 0;
        int left = Math.max(0, gain(node.left));
        int right = Math.max(0, gain(node.right));
        best = Math.max(best, node.val + left + right);
        return node.val + Math.max(left, right);
    }
}
""",
    },
    "climbing-stairs": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. To reach step `i` you can come from `i-1` (one step) or `i-2` (two steps), so `f(i) = f(i-1) + f(i-2)`.
2. That is the Fibonacci recurrence with base cases `f(1) = 1` and `f(2) = 2`.
3. Only the previous two values are needed, so iterate with two rolling variables.

Linear time and constant space instead of `O(2^n)` naive recursion.""",
        "hints": [
            "This is Fibonacci with slightly shifted base cases.",
            "Do not use plain recursion - it recomputes the same subproblems exponentially.",
            "Keep just two variables (prev2, prev1) instead of a full DP array.",
        ],
        "python": """
class Solution:
    def climbStairs(self, n):
        if n <= 2:
            return n
        prev2, prev1 = 1, 2
        for _ in range(3, n + 1):
            prev2, prev1 = prev1, prev1 + prev2
        return prev1
""",
        "javascript": """
var climbStairs = function(n) {
    if (n <= 2) return n;
    let prev2 = 1, prev1 = 2;
    for (let i = 3; i <= n; i++) {
        const cur = prev1 + prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
};
""",
        "java": """
class Solution {
    public int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;
        for (int i = 3; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""",
    },
    "climbing-stairs-ii": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. `dp[i]` is the minimum cost to reach step `i` (index `n` is the top, just past the last stair).
2. From step `i` you arrived either from `i-1` paying `cost[i-1]`, or from `i-2` paying `cost[i-2]`.
3. Recurrence: `dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])`.
4. Only the last two dp values are needed, so the array collapses into two variables.

The final answer is `dp[n]`, i.e. the cost of standing on the virtual step above the last stair.""",
        "hints": [
            "The goal is the step AFTER the last index, not the last index itself.",
            "When you pay cost[i] you are BUYING the right to stand on step i.",
            "Two rolling variables are enough - no full dp table required.",
        ],
        "python": """
class Solution:
    def minCostClimbingStairs(self, costs):
        prev2, prev1 = 0, 0
        for c in costs:
            cur = c + min(prev1, prev2)
            prev2, prev1 = prev1, cur
        return min(prev1, prev2)
""",
        "javascript": """
var minCostClimbingStairs = function(costs) {
    let prev2 = 0, prev1 = 0;
    for (const c of costs) {
        const cur = c + Math.min(prev1, prev2);
        prev2 = prev1;
        prev1 = cur;
    }
    return Math.min(prev1, prev2);
};
""",
        "java": """
class Solution {
    public int minCostClimbingStairs(int[] costs) {
        int prev2 = 0, prev1 = 0;
        for (int c : costs) {
            int cur = c + Math.min(prev1, prev2);
            prev2 = prev1;
            prev1 = cur;
        }
        return Math.min(prev1, prev2);
    }
}
""",
    },
    "clone-graph": {
        "time": "O(V + E)",
        "space": "O(V)",
        "explanation": """**Approach**

1. Use a hash map `clones` from original node -> its clone so every node is copied exactly once (this also breaks cycles).
2. BFS/DFS over the original graph: for each node, create its clone if missing, then clone all neighbors and connect them.
3. Because edges are symmetric in an undirected graph, the map guarantees each edge is wired from both sides without duplication.

Vertices `V` and edges `E` are each processed a constant number of times.""",
        "hints": [
            "Without a visited/cloned map you will recurse forever on cycles.",
            "Create the clone BEFORE recursing into neighbors - that is what marks the node as seen.",
            "A single-node graph with no neighbors should return a lone clone.",
        ],
        "python": """
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

class Solution:
    def cloneGraph(self, adjList):
        if not adjList:
            return []
        nodes = {i: Node(i) for i in range(1, len(adjList) + 1)}
        for i, nbs in enumerate(adjList, start=1):
            for nb in nbs:
                nodes[i].neighbors.append(nodes[nb])
        clones = {}

        def dfs(n):
            if n.val in clones:
                return clones[n.val]
            copy = Node(n.val)
            clones[n.val] = copy
            for nb in n.neighbors:
                copy.neighbors.append(dfs(nb))
            return copy

        dfs(nodes[1])
        return [[nb.val for nb in clones[i].neighbors]
                for i in range(1, len(adjList) + 1)]
""",
        "javascript": """
var Node = function(val, neighbors) {
    this.val = val === undefined ? 0 : val;
    this.neighbors = neighbors === undefined ? [] : neighbors;
};

var cloneGraph = function(adjList) {
    if (!adjList || !adjList.length) return [];
    const nodes = new Map();
    for (let i = 1; i <= adjList.length; i++) nodes.set(i, new Node(i, []));
    for (let i = 1; i <= adjList.length; i++) {
        for (const nb of adjList[i - 1]) nodes.get(i).neighbors.push(nodes.get(nb));
    }
    const clones = new Map();
    const dfs = (n) => {
        if (clones.has(n.val)) return clones.get(n.val);
        const copy = new Node(n.val, []);
        clones.set(n.val, copy);
        for (const nb of n.neighbors) copy.neighbors.push(dfs(nb));
        return copy;
    };
    dfs(nodes.get(1));
    const out = [];
    for (let i = 1; i <= adjList.length; i++) {
        out.push(clones.get(i).neighbors.map((nb) => nb.val));
    }
    return out;
};
""",
        "java": """
class Solution {
    static class Node {
        int val;
        List<Node> neighbors = new ArrayList<>();
        Node(int val) { this.val = val; }
    }

    public List<List<Integer>> cloneGraph(List<List<Integer>> adjList) {
        if (adjList == null || adjList.isEmpty()) return new ArrayList<>();
        int n = adjList.size();
        Node[] nodes = new Node[n + 1];
        for (int i = 1; i <= n; i++) nodes[i] = new Node(i);
        for (int i = 1; i <= n; i++) {
            for (int nb : adjList.get(i - 1)) nodes[i].neighbors.add(nodes[nb]);
        }
        Map<Integer, Node> clones = new HashMap<>();
        dfs(nodes[1], clones);
        List<List<Integer>> out = new ArrayList<>();
        for (int i = 1; i <= n; i++) {
            List<Integer> row = new ArrayList<>();
            for (Node nb : clones.get(i).neighbors) row.add(nb.val);
            out.add(row);
        }
        return out;
    }

    private Node dfs(Node n, Map<Integer, Node> clones) {
        if (clones.containsKey(n.val)) return clones.get(n.val);
        Node copy = new Node(n.val);
        clones.put(n.val, copy);
        for (Node nb : n.neighbors) copy.neighbors.add(dfs(nb, clones));
        return copy;
    }
}
""",
    },
    "coin-change": {
        "time": "O(amount * len(coins))",
        "space": "O(amount)",
        "explanation": """**Approach**

1. Bottom-up DP: `dp[x]` is the fewest coins that sum to amount `x`, initialized to `inf` with `dp[0] = 0`.
2. For every amount `x` and every coin `c <= x`, try `dp[x] = min(dp[x], dp[x - c] + 1)`.
3. The answer is `dp[amount]` if it is still `inf`, the answer is `-1` (impossible).

The order loops amounts outside and coins inside so each state is fully relaxed exactly once.""",
        "hints": [
            "Start from dp[0] = 0 and build upward; infinite means 'not reachable yet'.",
            "This is an unbounded knapsack - each coin may be reused any number of times.",
            "Return -1 when dp[amount] was never updated.",
        ],
        "python": """
class Solution:
    def coinChange(self, coins, amount):
        dp = [0] + [float('inf')] * amount
        for x in range(1, amount + 1):
            for c in coins:
                if c <= x and dp[x - c] + 1 < dp[x]:
                    dp[x] = dp[x - c] + 1
        return -1 if dp[amount] == float('inf') else dp[amount]
""",
        "javascript": """
var coinChange = function(coins, amount) {
    const dp = new Array(amount + 1).fill(Infinity);
    dp[0] = 0;
    for (let x = 1; x <= amount; x++) {
        for (const c of coins) {
            if (c <= x && dp[x - c] + 1 < dp[x]) dp[x] = dp[x - c] + 1;
        }
    }
    return dp[amount] === Infinity ? -1 : dp[amount];
};
""",
        "java": """
class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, Integer.MAX_VALUE);
        dp[0] = 0;
        for (int x = 1; x <= amount; x++) {
            for (int c : coins) {
                if (c <= x && dp[x - c] != Integer.MAX_VALUE && dp[x - c] + 1 < dp[x]) {
                    dp[x] = dp[x - c] + 1;
                }
            }
        }
        return dp[amount] == Integer.MAX_VALUE ? -1 : dp[amount];
    }
}
""",
    },
    "combination-sum": {
        "time": "O(2^(t/m))",
        "space": "O(t/m)",
        "explanation": """**Approach**

1. Sort candidates and recurse with an index so each combination stays non-decreasing (this removes permutations).
2. At each step either include `candidates[i]` (stay at `i`, because reuse is allowed) or skip to `i + 1`.
3. When the running sum exceeds the target, prune the branch immediately.
4. A leaf with `sum == target` contributes a copy of the current path.

Because elements are reused, an element can appear unboundedly - pruning keeps the search finite.""",
        "hints": [
            "Carry a start index so combinations are generated in sorted order (no duplicates).",
            "Reusing the SAME element means you recurse with i, not i + 1.",
            "Cut the branch as soon as the partial sum passes the target.",
        ],
        "python": """
class Solution:
    def combinationSum(self, candidates, target):
        candidates.sort()
        res = []

        def dfs(start, path, remaining):
            if remaining == 0:
                res.append(list(path))
                return
            for i in range(start, len(candidates)):
                c = candidates[i]
                if c > remaining:
                    break
                path.append(c)
                dfs(i, path, remaining - c)
                path.pop()

        dfs(0, [], target)
        return res
""",
        "javascript": """
var combinationSum = function(candidates, target) {
    candidates.sort((a, b) => a - b);
    const res = [];
    const dfs = (start, path, remaining) => {
        if (remaining === 0) { res.push([...path]); return; }
        for (let i = start; i < candidates.length; i++) {
            const c = candidates[i];
            if (c > remaining) break;
            path.push(c);
            dfs(i, path, remaining - c);
            path.pop();
        }
    };
    dfs(0, [], target);
    return res;
};
""",
        "java": """
class Solution {
    public List<List<Integer>> combinationSum(int[] candidates, int target) {
        Arrays.sort(candidates);
        List<List<Integer>> res = new ArrayList<>();
        dfs(candidates, 0, new ArrayList<>(), target, res);
        return res;
    }
    private void dfs(int[] c, int start, List<Integer> path, int rem, List<List<Integer>> res) {
        if (rem == 0) { res.add(new ArrayList<>(path)); return; }
        for (int i = start; i < c.length; i++) {
            if (c[i] > rem) break;
            path.add(c[i]);
            dfs(c, i, path, rem - c[i], res);
            path.remove(path.size() - 1);
        }
    }
}
""",
    },
    "container-with-most-water": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. Place two pointers at both ends; the area is `min(h[left], h[right]) * (right - left)`.
2. Record the maximum area seen.
3. Move the pointer at the **shorter** line inward: only that side can possibly increase the height, and the width only shrinks, so keeping the taller line can never produce a better area later.
4. Stop when the pointers meet.

One linear pass finds the optimum without checking all `O(n^2)` pairs.""",
        "hints": [
            "The width only decreases as you move - height must be the thing that improves.",
            "Always advance the shorter side; advancing the taller side can only shrink the area.",
            "Track the running maximum as you go rather than comparing at the end.",
        ],
        "python": """
class Solution:
    def maxArea(self, height):
        lo, hi = 0, len(height) - 1
        best = 0
        while lo < hi:
            area = min(height[lo], height[hi]) * (hi - lo)
            if area > best:
                best = area
            if height[lo] < height[hi]:
                lo += 1
            else:
                hi -= 1
        return best
""",
        "javascript": """
var maxArea = function(height) {
    let lo = 0, hi = height.length - 1, best = 0;
    while (lo < hi) {
        const area = Math.min(height[lo], height[hi]) * (hi - lo);
        if (area > best) best = area;
        if (height[lo] < height[hi]) lo++;
        else hi--;
    }
    return best;
};
""",
        "java": """
class Solution {
    public int maxArea(int[] height) {
        int lo = 0, hi = height.length - 1, best = 0;
        while (lo < hi) {
            int area = Math.min(height[lo], height[hi]) * (hi - lo);
            if (area > best) best = area;
            if (height[lo] < height[hi]) lo++;
            else hi--;
        }
        return best;
    }
}
""",
    },
    "contains-duplicate": {
        "time": "O(n)",
        "space": "O(n)",
        "explanation": """**Approach**

1. Sweep the array once while inserting every value into a hash set.
2. If a value is already present in the set, a duplicate exists - return `True` immediately.
3. Otherwise add it and continue; if the sweep finishes, all values were unique.

Both time and space are linear; sorting first would also work but costs `O(n log n)` time.""",
        "hints": [
            "A set gives O(1) average membership tests.",
            "Early return as soon as you see a repeat - no need to scan the rest.",
            "Sorting is an alternative, but it mutates the input and is slower.",
        ],
        "python": """
class Solution:
    def containsDuplicate(self, nums):
        seen = set()
        for n in nums:
            if n in seen:
                return True
            seen.add(n)
        return False
""",
        "javascript": """
var containsDuplicate = function(nums) {
    const seen = new Set();
    for (const n of nums) {
        if (seen.has(n)) return true;
        seen.add(n);
    }
    return false;
};
""",
        "java": """
class Solution {
    public boolean containsDuplicate(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int n : nums) {
            if (!seen.add(n)) return true;
        }
        return false;
    }
}
""",
    },
    "convert-sorted-array-to-bst": {
        "time": "O(n)",
        "space": "O(log n)",
        "explanation": """**Approach**

1. A balanced BST is built by always choosing the **ceiling midpoint** (`lo + (hi - lo + 1) // 2`) of the current range as the root.
2. Recurse on the left half for the left subtree and the right half for the right subtree.
3. The midpoint choice keeps the heights of both subtrees within one of each other, guaranteeing `O(log n)` depth.
4. Base case: an empty range returns `None`.

Each element becomes exactly one node, so construction is linear.""",
        "hints": [
            "mid = lo + (hi - lo + 1) // 2 - the ceiling midpoint gives a balanced split.",
            "Left range is [lo, mid - 1], right range is [mid + 1, hi].",
            "An empty range (lo > hi) is your recursion base case.",
        ],
        "python": """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def sortedArrayToBST(self, nums):
        def build(lo, hi):
            if lo > hi:
                return None
            mid = lo + (hi - lo + 1) // 2
            node = TreeNode(nums[mid])
            node.left = build(lo, mid - 1)
            node.right = build(mid + 1, hi)
            return node

        return build(0, len(nums) - 1)
""",
        "javascript": """
var sortedArrayToBST = function(nums) {
    const build = (lo, hi) => {
        if (lo > hi) return null;
        const mid = lo + (((hi - lo + 1)) >> 1);
        const node = new TreeNode(nums[mid]);
        node.left = build(lo, mid - 1);
        node.right = build(mid + 1, hi);
        return node;
    };
    return build(0, nums.length - 1);
};
""",
        "java": """
class Solution {
    public TreeNode sortedArrayToBST(int[] nums) {
        return build(nums, 0, nums.length - 1);
    }
    private TreeNode build(int[] nums, int lo, int hi) {
        if (lo > hi) return null;
        int mid = lo + (hi - lo + 1) / 2;
        TreeNode node = new TreeNode(nums[mid]);
        node.left = build(nums, lo, mid - 1);
        node.right = build(nums, mid + 1, hi);
        return node;
    }
}
""",
    },
    "count-and-say": {
        "time": "O(n * 2^n)",
        "space": "O(2^n)",
        "explanation": """**Approach**

1. Start from the seed `"1"` and iterate `n - 1` times.
2. In each iteration compress the current string into run-length form: count consecutive identical digits and append `count + digit`.
3. The result of one pass becomes the input of the next.

Every pass reads the whole string once; the string itself roughly doubles each round, hence the exponential bound.""",
        "hints": [
            "Build the next term from the current one - never recount a term you already passed.",
            "Group consecutive equal characters, then emit '<length><digit>'.",
            "n = 1 returns '1' without any iteration.",
        ],
        "python": """
class Solution:
    def countAndSay(self, n):
        s = '1'
        for _ in range(n - 1):
            nxt = []
            i = 0
            while i < len(s):
                j = i
                while j < len(s) and s[j] == s[i]:
                    j += 1
                nxt.append(str(j - i) + s[i])
                i = j
            s = ''.join(nxt)
        return s
""",
        "javascript": """
var countAndSay = function(n) {
    let s = '1';
    for (let it = 0; it < n - 1; it++) {
        let nxt = '';
        let i = 0;
        while (i < s.length) {
            let j = i;
            while (j < s.length && s[j] === s[i]) j++;
            nxt += String(j - i) + s[i];
            i = j;
        }
        s = nxt;
    }
    return s;
};
""",
        "java": """
class Solution {
    public String countAndSay(int n) {
        String s = "1";
        for (int it = 0; it < n - 1; it++) {
            StringBuilder sb = new StringBuilder();
            int i = 0;
            while (i < s.length()) {
                int j = i;
                while (j < s.length() && s.charAt(j) == s.charAt(i)) j++;
                sb.append(j - i).append(s.charAt(i));
                i = j;
            }
            s = sb.toString();
        }
        return s;
    }
}
""",
    },
    "count-even-numbers": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. A number is even exactly when `num % 2 == 0` (this also correctly classifies `0` and negatives).
2. Sweep the array once, incrementing a counter for every even value.
3. The counter alone is all the state you need.

Single pass, constant extra space.""",
        "hints": [
            "Use the modulo operator rather than converting to string.",
            "Zero is even - do not special-case it away.",
            "An empty array should simply return 0.",
        ],
        "python": """
class Solution:
    def countEvens(self, nums):
        count = 0
        for num in nums:
            if num % 2 == 0:
                count += 1
        return count
""",
        "javascript": """
var countEvens = function(nums) {
    let count = 0;
    for (const num of nums) if (num % 2 === 0) count++;
    return count;
};
""",
        "java": """
class Solution {
    public int countEvens(int[] nums) {
        int count = 0;
        for (int num : nums) if (num % 2 == 0) count++;
        return count;
    }
}
""",
    },
    "course-schedule": {
        "time": "O(V + E)",
        "space": "O(V + E)",
        "explanation": """**Approach**

1. Model each course as a node and each prerequisite `(a, b)` as a directed edge `b -> a` (b must come before a).
2. A valid schedule exists **iff** the graph is acyclic, which is exactly what topological sort checks.
3. Compute indegrees, enqueue all zero-indegree nodes, and repeatedly remove them while decrementing neighbors' indegrees (Kahn's algorithm).
4. If you process every node, no cycle exists - return `True`; a leftover node means a cycle - return `False`.

Each node and edge is touched a constant number of times.""",
        "hints": [
            "Cycle detection in a directed graph == can you finish a topological sort?",
            "Watch the edge direction: prerequisite (a, b) means b -> a.",
            "If fewer nodes are emitted than exist, a cycle is blocking the rest.",
        ],
        "python": """
class Solution:
    def canFinish(self, numCourses, prerequisites):
        adj = [[] for _ in range(numCourses)]
        indeg = [0] * numCourses
        for a, b in prerequisites:
            adj[b].append(a)
            indeg[a] += 1
        queue = [c for c in range(numCourses) if indeg[c] == 0]
        seen = 0
        while queue:
            c = queue.pop()
            seen += 1
            for nb in adj[c]:
                indeg[nb] -= 1
                if indeg[nb] == 0:
                    queue.append(nb)
        return seen == numCourses
""",
        "javascript": """
var canFinish = function(numCourses, prerequisites) {
    const adj = Array.from({ length: numCourses }, () => []);
    const indeg = new Array(numCourses).fill(0);
    for (const [a, b] of prerequisites) {
        adj[b].push(a);
        indeg[a]++;
    }
    const queue = [];
    for (let c = 0; c < numCourses; c++) if (indeg[c] === 0) queue.push(c);
    let seen = 0;
    while (queue.length) {
        const c = queue.shift();
        seen++;
        for (const nb of adj[c]) if (--indeg[nb] === 0) queue.push(nb);
    }
    return seen === numCourses;
};
""",
        "java": """
class Solution {
    public boolean canFinish(int numCourses, int[][] prerequisites) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) adj.add(new ArrayList<>());
        int[] indeg = new int[numCourses];
        for (int[] p : prerequisites) {
            adj.get(p[1]).add(p[0]);
            indeg[p[0]]++;
        }
        Queue<Integer> q = new LinkedList<>();
        for (int c = 0; c < numCourses; c++) if (indeg[c] == 0) q.add(c);
        int seen = 0;
        while (!q.isEmpty()) {
            int c = q.poll();
            seen++;
            for (int nb : adj.get(c)) if (--indeg[nb] == 0) q.add(nb);
        }
        return seen == numCourses;
    }
}
""",
    },
    "decode-ways": {
        "time": "O(n)",
        "space": "O(1)",
        "explanation": """**Approach**

1. `dp[i]` is the number of ways to decode the prefix `s[:i]`; `dp[0] = 1` (empty string has one decoding).
2. A single digit `s[i-1]` decodes if it is `'1'..'9'`: add `dp[i-1]`.
3. A two-digit code `s[i-2:i]` decodes if it is `'10'..'26'`: add `dp[i-2]`.
4. A `'0'` that cannot pair with `1` or `2` makes the whole string undecodable (all ways become 0).

Only the previous two dp values are needed.""",
        "hints": [
            "Treat '0' carefully: it is only valid as part of 10 or 20.",
            "Two transitions: take 1 digit (if 1-9) and take 2 digits (if 10-26).",
            "If any prefix becomes impossible, the final answer is 0.",
        ],
        "python": """
class Solution:
    def numDecodings(self, s):
        s = str(s)
        if not s or s[0] == '0':
            return 0
        prev2, prev1 = 1, 1
        for i in range(1, len(s)):
            cur = 0
            if s[i] != '0':
                cur = prev1
            two = int(s[i - 1:i + 1])
            if 10 <= two <= 26:
                cur += prev2
            prev2, prev1 = prev1, cur
            if prev1 == 0:
                return 0
        return prev1
""",
        "javascript": """
var numDecodings = function(s) {
    s = String(s);
    if (!s || s[0] === '0') return 0;
    let prev2 = 1, prev1 = 1;
    for (let i = 1; i < s.length; i++) {
        let cur = 0;
        if (s[i] !== '0') cur = prev1;
        const two = parseInt(s.slice(i - 1, i + 1), 10);
        if (two >= 10 && two <= 26) cur += prev2;
        prev2 = prev1;
        prev1 = cur;
        if (prev1 === 0) return 0;
    }
    return prev1;
};
""",
        "java": """
class Solution {
    public int numDecodings(String s) {
        if (s == null || s.length() == 0 || s.charAt(0) == '0') return 0;
        int prev2 = 1, prev1 = 1;
        for (int i = 1; i < s.length(); i++) {
            int cur = 0;
            if (s.charAt(i) != '0') cur = prev1;
            int two = Integer.parseInt(s.substring(i - 1, i + 1));
            if (two >= 10 && two <= 26) cur += prev2;
            prev2 = prev1;
            prev1 = cur;
            if (prev1 == 0) return 0;
        }
        return prev1;
    }
}
""",
    },
}
