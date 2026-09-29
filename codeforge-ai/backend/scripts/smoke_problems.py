"""E2E smoke test for the problems API (requires server on :8000)."""
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode())
        except Exception:
            payload = {"detail": "unparseable"}
        return exc.code, payload


status, auth = call("POST", "/auth/login", form={"username": "admin", "password": "admin123"})
assert status == 200, auth
token = auth["access_token"]
print("login OK")

# list envelope
status, body = call("GET", "/problems?limit=5", token=token)
assert status == 200, body
print("list:", {k: body[k] for k in ("total", "page", "limit")}, "items", len(body["items"]))
assert body["total"] >= 373 and len(body["items"]) == 5
assert {"is_solved", "is_favorite"} <= set(body["items"][0].keys())

# stats
status, stats = call("GET", "/problems/stats", token=token)
assert status == 200, stats
print("stats:", stats)
assert stats["total"] >= 373

# search route no longer shadowed by /problems/{problem_id}
status, res = call("GET", "/problems/search?q=two-sum", token=token)
assert status == 200, res
assert any(p["slug"] == "two-sum" for p in res), [p["slug"] for p in res]
print("search OK:", len(res), "results")

# detail: hidden test cases must not be exposed
status, detail = call("GET", "/problems/slug/two-sum", token=token)
assert status == 200, detail
tc = detail["test_cases"]
print("detail test_cases:", len(tc), "all public:", all(t["is_public"] for t in tc))
assert all(t["is_public"] for t in tc), "hidden testcase leaked in detail"
assert "reference_solution" not in detail

# topic filter
status, by_topic = call("GET", "/problems?topic=array&limit=500", token=token)
assert status == 200, by_topic
print("topic=array ->", by_topic["total"])
assert by_topic["total"] > 0

# difficulty filter
status, easy = call("GET", "/problems?difficulty=easy&limit=500", token=token)
assert status == 200 and easy["total"] > 0
print("easy ->", easy["total"])

# favorites round trip
pid = detail["id"]
status, r = call("POST", f"/problems/{pid}/favorite", token=token)
assert status == 200 and r["favorite"] is True, r
status, favs = call("GET", "/problems/favorites", token=token)
assert status == 200 and any(f["id"] == pid for f in favs), favs
status, detail2 = call("GET", "/problems/slug/two-sum", token=token)
assert detail2["is_favorite"] is True, detail2["is_favorite"]
status, r = call("DELETE", f"/problems/{pid}/favorite", token=token)
assert r["favorite"] is False, r
status, detail3 = call("GET", "/problems/slug/two-sum", token=token)
assert detail3["is_favorite"] is False
print("favorites round trip OK")

# anonymous access still works (flags default false)
status, anon = call("GET", "/problems/slug/two-sum")
assert status == 200 and anon["is_solved"] is False
print("anonymous detail OK")

print("PROBLEMS SMOKE OK")
