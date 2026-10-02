"""Payment / subscription schemas."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Plan = Literal["monthly", "annual"]
Provider = Literal["paypal", "paytm"]


class PlanResponse(BaseModel):
    id: str
    name: str
    interval: str  # month | year
    price_usd: float
    price_inr: float
    description: str
    features: list[str] = Field(default_factory=list)
    popular: bool = False


class CheckoutRequest(BaseModel):
    plan: Plan
    provider: Provider
    origin_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Frontend base URL the payment provider should redirect back to",
    )


class CheckoutResponse(BaseModel):
    subscription_id: str
    provider: str
    plan: str
    order_id: str
    redirect_url: str
    amount: float
    currency: str
    demo: bool
    # For paytm hosted-checkout POST flow: hidden form fields to submit.
    form_fields: dict[str, str] = Field(default_factory=dict)


class VerifyRequest(BaseModel):
    provider: Provider
    order_id: str = Field(..., min_length=3, max_length=120)
    params: dict[str, str] = Field(
        default_factory=dict,
        description="Provider callback query params (e.g. Paytm STATUS / CHECKSUMHASH)",
    )


class SubscriptionStatus(BaseModel):
    active: bool
    plan: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    days_left: Optional[int] = None
    is_admin: bool = False
