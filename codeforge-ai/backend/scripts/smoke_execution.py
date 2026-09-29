"""Quick E2E smoke test for run/submit execution (requires server on :8000).

Uses only the stdlib so it runs in a bare venv.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def call(method, path, token=None, body=None, form=None):
    data = None
    headers = {}
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


status, auth = call("POST", "/auth/login", form={"username": "admin", "password": "admin123"})
assert status == 200, auth
token = auth["access_token"]
print("login OK")

status, probs = call("GET", "/problems/slug/two-sum", token=token)
assert status == 200, probs
pid = probs["id"]
print("problem id:", pid)

GOOD = (
    "class Solution:\n"
    "    def twoSum(self, nums, target):\n"
    "        seen = {}\n"
    "        for i, x in enumerate(nums):\n"
    "            if target - x in seen:\n"
    "                return [seen[target - x], i]\n"
    "            seen[x] = i\n"
)
BAD = "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]\n"

status, j = call("POST", "/submissions", token=token, body={
    "problem_id": pid, "language": "python", "source_code": GOOD, "mode": "run",
})
print("RUN good ->", status, {k: j.get(k) for k in ("status", "mode", "id", "passed_count", "total_count", "runtime_ms")})
assert status == 201 and j["status"] == "accepted" and j["id"] is None, j

status, j = call("POST", "/submissions", token=token, body={
    "problem_id": pid, "language": "python", "source_code": BAD, "mode": "run",
})
print("RUN bad  ->", j["status"], f"{j['passed_count']}/{j['total_count']}")
assert j["status"] == "wrong_answer", j
failed = [t for t in j["test_results"] if not t["passed"]]
assert failed and all(t["is_public"] for t in j["test_results"]), j
print("  first failure:", json.dumps(failed[0]))

status, j = call("POST", "/submissions", token=token, body={
    "problem_id": pid, "language": "python", "source_code": GOOD, "mode": "submit",
})
print("SUBMIT   ->", j["status"], "id", j["id"], f"{j['passed_count']}/{j['total_count']}")
assert j["status"] == "accepted" and j["id"] is not None, j
assert all(t["is_public"] for t in j["test_results"]), "hidden case leaked!"

status, j = call("POST", "/submissions", token=token, body={
    "problem_id": pid, "language": "python",
    "source_code": "class Solution:\n  def twoSum( :\n   pass", "mode": "run",
})
print("RUN syntax->", j["status"], (j.get("error_message") or "")[:60])
assert j["status"] == "compilation_error", j

# javascript path (node available on this machine)
status, j = call("POST", "/submissions", token=token, body={
    "problem_id": pid, "language": "javascript",
    "source_code": "var twoSum = function(nums, target) {\n  const m = new Map();\n"
                   "  for (let i = 0; i < nums.length; i++) {\n"
                   "    const c = target - nums[i];\n"
                   "    if (m.has(c)) return [m.get(c), i];\n"
                   "    m.set(nums[i], i);\n  }\n  return [];\n};",
    "mode": "run",
})
print("RUN js    ->", j["status"], f"{j['passed_count']}/{j['total_count']}")
assert j["status"] == "accepted", j

print("SMOKE OK")
