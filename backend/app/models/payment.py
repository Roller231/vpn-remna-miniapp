import enum
from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Numeric, Boolean, DateTime, Enum, Text, ForeignKey,
    func, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethodType(str, enum.Enum):
    YOOKASSA = "yookassa"
    BALANCE = "balance"
    TELEGRAM_STARS = "telegram_stars"
    ADMIN_MANUAL = "admin_manual"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subscription_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    method: Mapped[PaymentMethodType] = mapped_column(
        Enum(PaymentMethodType), nullable=False
    )

    # External provider payment ID (e.g. YooKassa payment_id)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    # Idempotency key for provider calls
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Raw provider metadata (confirmation URL, receipt, etc.)
    provider_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # If this payment is a top-up (not a subscription purchase)
    is_topup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="payments")
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="payments"
    )

    __table_args__ = (
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_provider_payment_id", "provider_payment_id"),
    )


class PaymentMethod(Base):
    """Saved payment methods (provider binding tokens, not raw card data)."""
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    method_type: Mapped[PaymentMethodType] = mapped_column(Enum(PaymentMethodType), nullable=False)
    # Provider binding/token ID (NOT raw card data)
    provider_method_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_payment_methods_user_id", "user_id"),
    )
