import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Enum, Text,
    func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    BANNED = "banned"
    BLOCKED_BOT = "blocked_bot"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    # ^ Telegram user ID as primary key

    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )

    is_trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bot_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Auto-login short token (e.g. for links like /auth/t/Y2Wrrcp06vkFq36_)
    login_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)

    # For migration from old DB
    legacy_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subscription_token: Mapped[str | None] = mapped_column(String(512), nullable=True)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False)
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")
    referral_as_invitee: Mapped["Referral | None"] = relationship(
        "Referral", foreign_keys="Referral.invitee_id", back_populates="invitee", uselist=False
    )
    referral_as_referrer: Mapped[list["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.referrer_id", back_populates="referrer"
    )

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_legacy_id", "legacy_id"),
        Index("ix_users_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"
