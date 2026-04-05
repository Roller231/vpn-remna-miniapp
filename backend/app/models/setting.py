"""
AppSetting — key-value store for bot / mini-app configuration.
Managed from the admin panel; read by the public /settings endpoint.
"""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="If True, visible via public /settings endpoint"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<AppSetting key={self.key}>"
