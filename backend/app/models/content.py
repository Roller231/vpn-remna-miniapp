from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ContentPage(Base):
    """CMS-managed content pages (FAQ, ToS, onboarding, etc.)."""
    __tablename__ = "content_pages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_content_pages_key", "key"),)
