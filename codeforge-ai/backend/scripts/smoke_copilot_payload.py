"""Verify the exact payload shape the frontend copilot client sends."""
import json, urllib.request, urllib.error, urllib.parse

BASE = "http://127.0.0.1:8000/api"

def post(path, token, payload, ctype="application/json"):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", ctype)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read().decode()

# login (form-encoded like OAuth2PasswordRequestForm)
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(BASE + "/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
with urllib.request.urlopen(req, timeout=30) as r:
    token = json.loads(r.read())["access_token"]

payload = {
    "request_type": "explain_problem",
    "problem_id": 1,
    "language": "python",
    "code": "def twoSum(nums, target):\n    return []\n",
    "conversation_id": None,
    "message": None,
    "hint_level": 1,
    "run_result": {"status": "wrong_answer", "message": "1/3", "test_results": [{"passed": False}]},
}
status, ctype, body = post("/ai/copilot", token, payload)
print("JSON  ->", status, ctype, body[:220].replace("\n", " "))

payload2 = dict(payload, request_type="debug", conversation_id=1)
status2, ctype2, body2 = post("/ai/copilot/stream", token, payload2)
print("STREAM->", status2, ctype2)
print("   first event:", body2.split("\n\n")[0][:200])

# bad conversation_id (string) must NOT 422 from our client's perspective
status3, _, body3 = post("/ai/copilot", token, dict(payload, conversation_id="abc"))
print("BAD ID->", status3, body3[:160])
