from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Numeric, Integer, Boolean, DateTime, Text,
    Float, ForeignKey, func, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Product(Base):
    """A product is a VPN subscription offering (e.g. 'Standard', 'Pro')."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Remnawave inbound/config template UUID
    remnawave_inbound_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    plans: Mapped[list["Plan"]] = relationship("Plan", back_populates="product")


class Plan(Base):
    """
    A plan is a specific pricing tier for a product.
    e.g. Standard / 1 month / 1 device / 299 RUB
    """
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    devices: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Discount price (None = no discount)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Telegram Stars price (None = Stars payment disabled for this plan)
    price_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Traffic policy
    traffic_limit_gb: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = unlimited
    traffic_reset_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    traffic_reset_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    traffic_notify_percent: Mapped[int] = mapped_column(Integer, default=80, nullable=False)

    # Features
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_auto_renewal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_visible_in_catalog: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Extra metadata (JSON)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship("Product", back_populates="plans")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        Index("ix_plans_product_id", "product_id"),
        Index("ix_plans_is_active", "is_active"),
    )
