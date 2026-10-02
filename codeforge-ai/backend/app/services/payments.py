"""Payment provider integration: PayPal, Paytm, with a demo fallback.

When provider credentials are not configured (empty env vars) the service runs
in *demo mode*: orders are created locally and verification always succeeds,
so the full subscribe -> verify -> unlock flow can be exercised end to end
without merchant accounts.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Optional

import httpx

from app.core.config import settings


class PaymentError(Exception):
    """Provider communication / verification failure."""


def is_demo(provider: str) -> bool:
    if provider == "paypal":
        return not (settings.paypal_client_id and settings.paypal_secret)
    if provider == "paytm":
        return not (settings.paytm_mid and settings.paytm_key)
    raise PaymentError(f"Unknown provider: {provider}")


def new_order_id(provider: str) -> str:
    if is_demo(provider):
        return f"DEMO-{provider.upper()}-{secrets.token_hex(6).upper()}"
    if provider == "paypal":
        # PayPal assigns the order id itself; a placeholder is replaced on create.
        return ""
    return f"CF{secrets.token_hex(8).upper()}"


# --------------------------------------------------------------------------
# Paytm checksum (official algorithm: sorted "k|v|" string + salt, SHA-256,
# base64-encoded, keyed with the merchant key via HMAC).
# --------------------------------------------------------------------------

def paytm_checksum(params: dict[str, str], salt: Optional[str] = None) -> str:
    salt = salt if salt is not None else secrets.token_hex(4)
    keys = sorted(k for k in params if k.lower() != "checksumhash")
    raw = "".join(f"{k}|{params[k]}|" for k in keys) + salt
    digest = hmac.new(settings.paytm_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii") + salt


def verify_paytm_checksum(params: dict[str, str]) -> bool:
    provided = params.get("CHECKSUMHASH") or params.get("checksumhash")
    if not provided or not settings.paytm_key:
        return False
    salt = provided[-8:]
    keys = sorted(k for k in params if k.lower() != "checksumhash")
    raw = "".join(f"{k}|{params[k]}|" for k in keys) + salt
    digest = hmac.new(settings.paytm_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii") + salt
    # constant-time compare
    return hmac.compare_digest(expected, provided)


# --------------------------------------------------------------------------
# PayPal Orders API v2
# --------------------------------------------------------------------------

def _paypal_base() -> str:
    host = "api-m.sandbox.paypal.com" if settings.paypal_mode != "live" else "api-m.live.paypal.com"
    return f"https://{host}"


def _paypal_token() -> str:
    try:
        resp = httpx.post(
            f"{_paypal_base()}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.paypal_client_id, settings.paypal_secret),
            headers={"Accept": "application/json"},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise PaymentError(f"PayPal unreachable: {exc}") from exc
    if resp.status_code != 200:
        raise PaymentError(f"PayPal auth failed ({resp.status_code})")
    token = resp.json().get("access_token")
    if not token:
        raise PaymentError("PayPal auth returned no token")
    return token


def create_paypal_order(
    amount: float,
    currency: str,
    return_url: str,
    cancel_url: str,
    label: str,
) -> dict:
    token = _paypal_token()
    try:
        resp = httpx.post(
            f"{_paypal_base()}/v2/checkout/orders",
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "description": label,
                        "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                    }
                ],
                "application_context": {
                    "brand_name": settings.project_name,
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "user_action": "PAY_NOW",
                },
            },
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise PaymentError(f"PayPal unreachable: {exc}") from exc
    if resp.status_code not in (200, 201):
        raise PaymentError(f"PayPal order creation failed ({resp.status_code}): {resp.text[:200]}")
    data = resp.json()
    approve_url = next(
        (l["href"] for l in data.get("links", []) if l.get("rel") in ("approve", "payer-action")),
        None,
    )
    if not approve_url:
        raise PaymentError("PayPal order missing approval link")
    return {"order_id": data["id"], "redirect_url": approve_url}


def verify_paypal_order(order_id: str) -> tuple[bool, Optional[str]]:
    token = _paypal_token()
    try:
        resp = httpx.post(
            f"{_paypal_base()}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise PaymentError(f"PayPal unreachable: {exc}") from exc
    if resp.status_code == 422:
        # ALREADY_CAPTURED / ORDER_NOT_APPROVED etc. - inspect status.
        detail = json.dumps(resp.json().get("details", []))
        return ("ORDER_NOT_APPROVED" not in detail), detail[:300]
    if resp.status_code not in (200, 201):
        raise PaymentError(f"PayPal capture failed ({resp.status_code}): {resp.text[:200]}")
    data = resp.json()
    status = data.get("status")
    if status == "COMPLETED":
        payer = (data.get("payer") or {}).get("email_address")
        return True, payer
    return False, status


# --------------------------------------------------------------------------
# Paytm hosted checkout + status verification
# --------------------------------------------------------------------------

def _paytm_host() -> str:
    return (
        "securegw.paytm.in" if settings.paytm_mode == "live" else "securegw-stage.paytm.in"
    )


def create_paytm_payment(order_id: str, amount: float, callback_url: str) -> dict:
    fields = {
        "mid": settings.paytm_mid,
        "orderId": order_id,
        "amount": f"{amount:.2f}",
        "channelId": "WEB",
        "txnTypeId": "payment",
        "website": settings.paytm_website,
        "callbackUrl": callback_url,
    }
    fields["checksumhash"] = paytm_checksum(fields)
    return {
        "order_id": order_id,
        "redirect_url": f"https://{_paytm_host()}/theia/ProcessTransaction",
        "form_fields": fields,
    }


def verify_paytm_payment(order_id: str, params: dict[str, str]) -> tuple[bool, Optional[str]]:
    # Path A: full callback params with checksum (hosted gateway redirect).
    if params.get("STATUS") and params.get("CHECKSUMHASH"):
        if not verify_paytm_checksum(params):
            return False, "checksum mismatch"
        return (params["STATUS"].upper() == "TXN_SUCCESS", params.get("TXNID"))

    # Path B: ask Paytm for the transaction status directly.
    status_body = {
        "mid": settings.paytm_mid,
        "orderId": order_id,
    }
    status_body["checksumhash"] = paytm_checksum(status_body)
    host = _paytm_host()
    try:
        resp = httpx.post(
            f"https://{host}/merchant-status/getTxnStatus",
            data=status_body,
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise PaymentError(f"Paytm unreachable: {exc}") from exc
    if resp.status_code != 200:
        raise PaymentError(f"Paytm status check failed ({resp.status_code})")
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    status = str(data.get("status", "")).upper()
    if not status:
        # Some gateways return form-encoded; fall back to text scan.
        status = "TXN_SUCCESS" if "TXN_SUCCESS" in resp.text else ""
    return (status == "TXN_SUCCESS", data.get("txnId") or data.get("TXNID"))


# --------------------------------------------------------------------------
# Unified entry points
# --------------------------------------------------------------------------

def create_payment(
    provider: str,
    order_id: str,
    amount: float,
    currency: str,
    return_url: str,
    cancel_url: str,
    label: str,
    callback_url: str = "",
) -> dict:
    """Return {order_id, redirect_url, form_fields, demo}."""
    if is_demo(provider):
        return {
            "order_id": order_id or new_order_id(provider),
            "redirect_url": return_url,
            "form_fields": {},
            "demo": True,
        }
    if provider == "paypal":
        result = create_paypal_order(amount, currency, return_url, cancel_url, label)
        return {"order_id": result["order_id"], "redirect_url": result["redirect_url"], "form_fields": {}, "demo": False}
    if provider == "paytm":
        result = create_paytm_payment(order_id, amount, callback_url or return_url)
        return {"order_id": result["order_id"], "redirect_url": result["redirect_url"], "form_fields": result["form_fields"], "demo": False}
    raise PaymentError(f"Unknown provider: {provider}")


def verify_payment(provider: str, order_id: str, params: dict[str, str]) -> tuple[bool, Optional[str]]:
    """Return (success, provider_reference)."""
    if is_demo(provider):
        if not order_id.startswith("DEMO-"):
            raise PaymentError("Unknown demo order")
        return True, f"demo-{secrets.token_hex(4)}"
    if provider == "paypal":
        return verify_paypal_order(order_id)
    if provider == "paytm":
        return verify_paytm_payment(order_id, params)
    raise PaymentError(f"Unknown provider: {provider}")
