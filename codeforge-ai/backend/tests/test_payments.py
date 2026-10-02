"""Payment flow and premium (Medium/Hard) gating tests.

The engine is swapped to an isolated in-memory SQLite database BEFORE the app
is imported, so these tests never touch the committed dev database.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import app.core.database as database

_memory_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
database.engine = _memory_engine
database.SessionLocal.configure(bind=_memory_engine)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def _seed_problems() -> None:
    """Insert one published problem per difficulty into the in-memory DB."""
    from app.models.problem import Problem, ProblemStatus

    db = database.SessionLocal()
    try:
        if db.query(Problem).count() == 0:
            for diff in ("easy", "medium", "hard"):
                db.add(
                    Problem(
                        title=f"Sample {diff.capitalize()}",
                        slug=f"sample-{diff}",
                        difficulty=diff,
                        description="Return the result.",
                        status=ProblemStatus.PUBLISHED.value,
                        topics='["array"]',
                        starter_code='{"python": "class Solution:\\n    pass"}',
                    )
                )
            db.commit()
    finally:
        db.close()


_seed_problems()

_USERNAME_SEQ = {"n": 0}


def _register() -> tuple[str, str]:
    """Register a fresh user; returns (token, username)."""
    _USERNAME_SEQ["n"] += 1
    username = f"payuser{_USERNAME_SEQ['n']}"
    email = f"{username}@example.com"
    res = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert res.status_code in (200, 201), res.text
    data = res.json()
    return data["access_token"], username


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _problems(token: str) -> list[dict]:
    res = client.get("/api/problems?limit=500", headers=_auth(token))
    assert res.status_code == 200, res.text
    return res.json()["items"]


# --------------------------------------------------------------------------
# Paytm checksum
# --------------------------------------------------------------------------

def test_paytm_checksum_roundtrip(monkeypatch):
    from app.core.config import settings
    from app.services import payments

    monkeypatch.setattr(settings, "paytm_key", "test_merchant_key")
    params = {"orderId": "CF123", "mid": "TESTMID", "amount": "299.00"}
    checksum = payments.paytm_checksum(params)
    assert payments.verify_paytm_checksum({**params, "CHECKSUMHASH": checksum})
    # tampered amount must fail
    assert not payments.verify_paytm_checksum({**params, "amount": "1.00", "CHECKSUMHASH": checksum})


# --------------------------------------------------------------------------
# Plans
# --------------------------------------------------------------------------

def test_plans_endpoint():
    res = client.get("/api/payments/plans")
    assert res.status_code == 200
    plans = res.json()
    assert [p["id"] for p in plans] == ["monthly", "annual"]
    assert plans[0]["price_usd"] > 0 and plans[0]["price_inr"] > 0
    assert plans[1]["popular"] is True


# --------------------------------------------------------------------------
# Premium gating
# --------------------------------------------------------------------------

def test_medium_hard_locked_for_free_user():
    token, _ = _register()
    items = _problems(token)
    by_diff = {"easy": None, "medium": None, "hard": None}
    for p in items:
        if p["difficulty"] in by_diff and by_diff[p["difficulty"]] is None:
            by_diff[p["difficulty"]] = p
    assert all(by_diff.values()), "seed data must contain all difficulties"

    assert by_diff["easy"]["is_locked"] is False
    assert by_diff["medium"]["is_locked"] is True
    assert by_diff["hard"]["is_locked"] is True

    # easy detail is visible
    res = client.get(f"/api/problems/slug/{by_diff['easy']['slug']}", headers=_auth(token))
    assert res.status_code == 200

    # medium detail is paywalled with a structured 402
    res = client.get(f"/api/problems/slug/{by_diff['medium']['slug']}", headers=_auth(token))
    assert res.status_code == 402
    detail = res.json()["detail"]
    assert detail["code"] == "PREMIUM_REQUIRED"
    assert detail["details"]["difficulty"] == "medium"

    # hard detail is paywalled too (even without login it must not leak)
    res = client.get(f"/api/problems/slug/{by_diff['hard']['slug']}")
    assert res.status_code == 402

    # submissions against a locked problem are refused before execution
    res = client.post(
        "/api/submissions",
        headers=_auth(token),
        json={
            "problem_id": by_diff["medium"]["id"],
            "language": "python",
            "source_code": "class Solution:\n    pass",
            "mode": "run",
        },
    )
    assert res.status_code == 402


# --------------------------------------------------------------------------
# Demo checkout -> verify -> unlock
# --------------------------------------------------------------------------

def test_demo_checkout_and_verify_unlocks_premium():
    token, _ = _register()
    headers = _auth(token)

    # no subscription yet
    res = client.get("/api/payments/subscription", headers=headers)
    assert res.status_code == 200
    assert res.json()["active"] is False

    medium = next(p for p in _problems(token) if p["difficulty"] == "medium")

    # checkout (demo mode: no PayPal credentials configured)
    res = client.post(
        "/api/payments/checkout",
        headers=headers,
        json={"plan": "monthly", "provider": "paypal", "origin_url": "http://localhost:5173"},
    )
    assert res.status_code == 200, res.text
    checkout = res.json()
    assert checkout["demo"] is True
    assert checkout["order_id"].startswith("DEMO-PAYPAL")
    assert checkout["amount"] > 0 and checkout["currency"] == "USD"

    # verifying activates the subscription
    res = client.post(
        "/api/payments/verify",
        headers=headers,
        json={"provider": "paypal", "order_id": checkout["order_id"]},
    )
    assert res.status_code == 200, res.text
    status = res.json()
    assert status["active"] is True
    assert status["plan"] == "monthly"
    assert status["days_left"] is not None and status["days_left"] >= 29

    # medium/hard are now unlocked
    res = client.get(f"/api/problems/slug/{medium['slug']}", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_locked"] is False

    items = _problems(token)
    assert all(p["is_locked"] is False for p in items)

    # verify is idempotent (page refresh)
    res = client.post(
        "/api/payments/verify",
        headers=headers,
        json={"provider": "paypal", "order_id": checkout["order_id"]},
    )
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_paytm_demo_checkout():
    token, _ = _register()
    headers = _auth(token)
    res = client.post(
        "/api/payments/checkout",
        headers=headers,
        json={"plan": "annual", "provider": "paytm", "origin_url": "http://localhost:5173"},
    )
    assert res.status_code == 200, res.text
    checkout = res.json()
    assert checkout["demo"] is True
    assert checkout["order_id"].startswith("DEMO-PAYTM")
    assert checkout["currency"] == "INR"

    res = client.post(
        "/api/payments/verify",
        headers=headers,
        json={"provider": "paytm", "order_id": checkout["order_id"]},
    )
    assert res.status_code == 200, res.text
    status = res.json()
    assert status["active"] is True
    assert status["plan"] == "annual"
    assert status["days_left"] >= 364


def test_verify_unknown_order_rejected():
    token, _ = _register()
    res = client.post(
        "/api/payments/verify",
        headers=_auth(token),
        json={"provider": "paypal", "order_id": "DEMO-PAYPAL-NOPE"},
    )
    assert res.status_code == 422


def test_second_checkout_blocked_while_active():
    token, _ = _register()
    headers = _auth(token)
    res = client.post(
        "/api/payments/checkout",
        headers=headers,
        json={"plan": "monthly", "provider": "paypal", "origin_url": "http://localhost:5173"},
    )
    order_id = res.json()["order_id"]
    client.post(
        "/api/payments/verify",
        headers=headers,
        json={"provider": "paypal", "order_id": order_id},
    )
    res = client.post(
        "/api/payments/checkout",
        headers=headers,
        json={"plan": "annual", "provider": "paytm", "origin_url": "http://localhost:5173"},
    )
    assert res.status_code == 422


def test_expired_subscription_relocks():
    token, _ = _register()
    headers = _auth(token)
    medium = next(p for p in _problems(token) if p["difficulty"] == "medium")

    res = client.post(
        "/api/payments/checkout",
        headers=headers,
        json={"plan": "monthly", "provider": "paypal", "origin_url": "http://localhost:5173"},
    )
    order_id = res.json()["order_id"]
    client.post(
        "/api/payments/verify",
        headers=headers,
        json={"provider": "paypal", "order_id": order_id},
    )
    assert client.get(f"/api/problems/slug/{medium['slug']}", headers=headers).status_code == 200

    # force this user's subscription into the past
    from datetime import timedelta
    from app.models.subscription import UserSubscription, utcnow_naive

    me = client.get("/api/auth/me", headers=headers).json()
    db = database.SessionLocal()
    try:
        sub = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == me["id"], UserSubscription.status == "active")
            .first()
        )
        assert sub is not None
        sub.expires_at = utcnow_naive() - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/payments/subscription", headers=headers)
    assert res.json()["active"] is False

    res = client.get(f"/api/problems/slug/{medium['slug']}", headers=headers)
    assert res.status_code == 402


def test_admin_bypasses_paywall():
    token, _ = _register()
    headers = _auth(token)
    from app.models.user import User

    me = client.get("/api/auth/me", headers=headers).json()
    db = database.SessionLocal()
    try:
        user = db.query(User).filter(User.id == me["id"]).first()
        user.role = "ADMIN"
        db.commit()
    finally:
        db.close()

    items = _problems(token)
    assert all(p["is_locked"] is False for p in items)
    hard = next(p for p in items if p["difficulty"] == "hard")
    res = client.get(f"/api/problems/slug/{hard['slug']}", headers=headers)
    assert res.status_code == 200
