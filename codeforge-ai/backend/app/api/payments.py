"""Payments / subscriptions API routes."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.security import require_user
from app.models.subscription import UserSubscription, utcnow_naive
from app.models.user import User
from app.schemas.payment import (
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    SubscriptionStatus,
    VerifyRequest,
)
from app.services import payments as payment_service

router = APIRouter()

PLAN_INTERVALS = {"monthly": 30, "annual": 365}


def _plans() -> list[PlanResponse]:
    return [
        PlanResponse(
            id="monthly",
            name="Monthly",
            interval="month",
            price_usd=settings.price_monthly_usd,
            price_inr=settings.price_monthly_inr,
            description="Full access, billed every month. Cancel anytime.",
            features=[
                "Unlock all Medium problems",
                "Unlock all Hard problems",
                "AI copilot & hints",
                "Full submission history",
            ],
            popular=False,
        ),
        PlanResponse(
            id="annual",
            name="Annual",
            interval="year",
            price_usd=settings.price_annual_usd,
            price_inr=settings.price_annual_inr,
            description="Best value - two months free versus monthly billing.",
            features=[
                "Everything in Monthly",
                "Priority AI copilot",
                "Early access to new problems",
                "Best price per month",
            ],
            popular=True,
        ),
    ]


def _price(plan: str, provider: str) -> tuple[float, str]:
    if provider == "paypal":
        return (settings.price_annual_usd if plan == "annual" else settings.price_monthly_usd, "USD")
    return (settings.price_annual_inr if plan == "annual" else settings.price_monthly_inr, "INR")


def _load_subscription(db: Session, user_id: int) -> Optional[UserSubscription]:
    return (
        db.query(UserSubscription)
        .filter(UserSubscription.user_id == user_id)
        .order_by(UserSubscription.id.desc())
        .first()
    )


def _status_for(db: Session, user: User) -> SubscriptionStatus:
    sub = _load_subscription(db, user.id)
    if sub and sub.status == "active" and sub.expires_at and sub.expires_at <= utcnow_naive():
        sub.status = "expired"
        db.commit()
    active = bool(sub and sub.is_active)
    days_left = None
    if active and sub.expires_at:
        days_left = max(0, (sub.expires_at - utcnow_naive()).days)
    return SubscriptionStatus(
        active=active,
        plan=sub.plan if sub else None,
        provider=sub.provider if sub else None,
        status=sub.status if sub else None,
        amount=sub.amount if sub else None,
        currency=sub.currency if sub else None,
        starts_at=sub.starts_at.isoformat() if sub and sub.starts_at else None,
        expires_at=sub.expires_at.isoformat() if sub and sub.expires_at else None,
        days_left=days_left,
        is_admin=user.role == "ADMIN",
    )


@router.get("/payments/plans", response_model=list[PlanResponse])
async def list_plans():
    return _plans()


@router.get("/payments/subscription", response_model=SubscriptionStatus)
async def current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    return _status_for(db, current_user)


@router.post("/payments/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    existing = _status_for(db, current_user)
    if existing.active:
        raise ValidationError("Subscription is already active")

    # a fresh checkout supersedes any stale pending attempt
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.status == "pending",
    ).delete()
    db.commit()

    origin = (body.origin_url or str(request.base_url)).rstrip("/")
    if origin.endswith("/api"):
        origin = origin[: -len("/api")]
    amount, currency = _price(body.plan, body.provider)
    local_order_id = payment_service.new_order_id(body.provider)

    if body.provider == "paytm":
        return_url = f"{origin}/payment/verify?provider=paytm&order_id={local_order_id}"
        cancel_url = f"{origin}/payment?cancelled=1"
        callback_url = return_url
    else:
        # PayPal appends ?token=<order_id> on approval; demo mode already knows it.
        return_url = (
            f"{origin}/payment/verify?provider=paypal&order_id={local_order_id}"
            if local_order_id
            else f"{origin}/payment/verify?provider=paypal"
        )
        cancel_url = f"{origin}/payment?cancelled=1"
        callback_url = ""

    sub = UserSubscription(
        user_id=current_user.id,
        plan=body.plan,
        provider=body.provider,
        status="pending",
        amount=amount,
        currency=currency,
        provider_order_id=local_order_id or "",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    try:
        created = payment_service.create_payment(
            provider=body.provider,
            order_id=local_order_id,
            amount=amount,
            currency=currency,
            return_url=return_url,
            cancel_url=cancel_url,
            label=f"{settings.project_name} {body.plan} subscription",
            callback_url=callback_url,
        )
    except payment_service.PaymentError as exc:
        sub.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")

    sub.provider_order_id = created["order_id"]
    db.commit()

    return CheckoutResponse(
        subscription_id=sub.public_id,
        provider=body.provider,
        plan=body.plan,
        order_id=created["order_id"],
        redirect_url=created["redirect_url"],
        amount=amount,
        currency=currency,
        demo=created["demo"],
        form_fields=created["form_fields"],
    )


@router.post("/payments/verify", response_model=SubscriptionStatus)
async def verify_payment(
    body: VerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    sub = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.provider == body.provider,
            UserSubscription.provider_order_id == body.order_id,
        )
        .order_by(UserSubscription.id.desc())
        .first()
    )
    if not sub:
        raise ValidationError("Order not found for this account")

    # idempotent: refreshing the verify page keeps the active state
    if sub.status == "active" and sub.is_active:
        return _status_for(db, current_user)

    try:
        success, reference = payment_service.verify_payment(
            body.provider, body.order_id, body.params
        )
    except payment_service.PaymentError as exc:
        raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")

    if not success:
        sub.status = "failed"
        db.commit()
        raise ValidationError(
            "Payment was not completed",
            details={"order_id": body.order_id, "provider": body.provider},
        )

    now = utcnow_naive()
    sub.status = "active"
    sub.provider_payment_id = reference
    sub.starts_at = now
    sub.expires_at = now + timedelta(days=PLAN_INTERVALS.get(sub.plan, 30))
    db.commit()

    return _status_for(db, current_user)
