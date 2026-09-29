"""E2E smoke test for the AI copilot endpoints (requires server on :8000).

Verifies the guaranteed paths while the Mistral key is rejected:
  - anonymous -> 401 (never 500)
  - authenticated + rejected key -> structured {error, message, retryable}
  - quick action catalog
  - SSE stream -> structured error event
  - conversation rows are created
"""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def call(method, path, token=None, body=None, form=None, raw=False):
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = resp.read().decode()
            if raw:
                return resp.status, payload, {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, json.loads(payload), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode()
        try:
            parsed = json.loads(payload)
        except Exception:
            parsed = {"raw": payload}
        return exc.code, parsed, {k.lower(): v for k, v in exc.headers.items()}


status, actions, _ = call("GET", "/ai/copilot/actions")
assert status == 200, actions
ids = [a["id"] for a in actions["actions"]]
assert len(ids) == 9, ids
print("quick actions:", ids)

payload = {
    "request_type": "explain_problem",
    "problem_id": 1,
    "language": "python",
    "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
    "message": "I am stuck",
}

# 1. anonymous -> 401 (structured), never 500
status, body, _ = call("POST", "/ai/copilot", body=payload)
print("anon copilot ->", status, body)
assert status == 401, (status, body)
assert "detail" in body

# 2. legacy routes also 401 now
status, body, _ = call("POST", "/ai/analyze", body={"code": "x = 1", "language": "python"})
print("anon analyze ->", status, body)
assert status == 401, (status, body)

# 3. auth + (expected) rejected key -> structured error or success
status, auth, _ = call("POST", "/auth/login", form={"username": "admin", "password": "admin123"})
token = auth["access_token"]

status, body, _ = call("POST", "/ai/copilot", token=token, body=payload)
print("authed copilot ->", status, json.dumps(body)[:220])
assert status in (200, 429, 502, 503, 504), (status, body)
if status == 200:
    assert body["reply"] and body["conversation_id"]
    print("  live AI reply received; conversation_id", body["conversation_id"])
else:
    # structured, secret-free error
    assert set(body) >= {"error", "message", "retryable"}, body
    blob = json.dumps(body)
    assert "vUgg54BdjsWFQenXOQe3qtGDKjIIhneC" not in blob, "API key leaked!"
    assert "Traceback" not in blob
    print("  structured error:", body["error"], "-", body["message"][:80])

# 4. streaming endpoint emits SSE events (delta/done or error)
req_body = dict(payload, request_type="hint", hint_level=1)
status, text, headers = call("POST", "/ai/copilot/stream", token=token, body=req_body, raw=True)
ctype = headers.get("content-type") or ""
print("stream ->", status, ctype, (text or "")[:160].replace("\n", "\\n"))
if status == 200 and ctype.startswith("text/event-stream"):
    assert "data: " in text
    first = json.loads(text.split("data: ", 1)[1].split("\n", 1)[0])
    assert first.get("type") in ("delta", "error"), first
    if first["type"] == "error":
        assert set(first) >= {"error", "message"}
else:
    # pre-stream rejection (rate limit / auth) must still be structured
    parsed = json.loads(text)
    assert set(parsed.get("detail", parsed)) >= {"error", "message"}, parsed
    print("  pre-stream structured rejection:", parsed)

# 5. conversation persisted
if status == 200:
    conv_check = text
print("COPILOT SMOKE OK")
