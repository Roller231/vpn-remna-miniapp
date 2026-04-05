import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Enum, Text, ForeignKey,
    Float, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    PENDING = "pending"
    TRIAL = "trial"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False
    )

    # Remnawave external reference
    remnawave_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)
    subscription_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Traffic
    traffic_limit_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    traffic_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    traffic_reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Devices
    devices_limit: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)

    # Auto-renewal
    is_auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Notifications sent flags
    notify_3d_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_1d_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_traffic_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="subscription")

    __table_args__ = (
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_remnawave_uuid", "remnawave_uuid"),
        Index("ix_subscriptions_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} user_id={self.user_id} status={self.status}>"
