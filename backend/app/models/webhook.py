import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Enum, Text, func, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WebhookSource(str, enum.Enum):
    REMNAWAVE = "remnawave"
    YOOKASSA = "yookassa"
    TELEGRAM = "telegram"


class WebhookEventLog(Base):
    __tablename__ = "webhook_events_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[WebhookSource] = mapped_column(Enum(WebhookSource), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    # External event ID for idempotency
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_webhook_events_log_source", "source"),
        Index("ix_webhook_events_log_external_id", "external_id"),
        Index("ix_webhook_events_log_is_processed", "is_processed"),
    )
