"""User subscription (premium access) model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow_naive() -> datetime:
    """Current UTC time without tzinfo (matches naive DateTime columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly | annual
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # paypal | paytm
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending | active | failed | expired
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    provider_order_id: Mapped[str] = mapped_column(String(120), index=True)
    provider_payment_id: Mapped[str] = mapped_column(String(120), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @property
    def is_active(self) -> bool:
        if self.status != "active" or not self.expires_at:
            return False
        return self.expires_at > utcnow_naive()

    def __repr__(self):
        return f"<UserSubscription user={self.user_id} plan={self.plan} status={self.status}>"
