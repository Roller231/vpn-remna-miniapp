import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Enum, Text, ForeignKey, func, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Inline keyboard buttons JSON: [[{text, url|callback_data}]]
    buttons: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class NotificationJob(Base):
    __tablename__ = "notification_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    template_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    buttons: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_notification_jobs_user_id", "user_id"),
        Index("ix_notification_jobs_status", "status"),
        Index("ix_notification_jobs_scheduled_at", "scheduled_at"),
    )
