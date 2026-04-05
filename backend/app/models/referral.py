from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger, Numeric, DateTime, ForeignKey, func, Index, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Referral(Base):
    """Maps invitee → referrer (who invited whom)."""
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    invitee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    referrer: Mapped["User"] = relationship(
        "User", foreign_keys=[referrer_id], back_populates="referral_as_referrer"
    )
    invitee: Mapped["User"] = relationship(
        "User", foreign_keys=[invitee_id], back_populates="referral_as_invitee"
    )
    rewards: Mapped[list["ReferralReward"]] = relationship("ReferralReward", back_populates="referral")

    __table_args__ = (
        Index("ix_referrals_referrer_id", "referrer_id"),
        Index("ix_referrals_invitee_id", "invitee_id"),
    )


class ReferralReward(Base):
    """Cashback earned by referrer per invitee payment."""
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referral_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False
    )
    payment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_credited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    credited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    referral: Mapped["Referral"] = relationship("Referral", back_populates="rewards")

    __table_args__ = (
        Index("ix_referral_rewards_referral_id", "referral_id"),
    )
