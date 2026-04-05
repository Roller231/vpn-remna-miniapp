from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "VPN Remna API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    APP_URL: str = "http://localhost:8000/api/v1"  # Base URL exposed to users (login links)
    MINIAPP_URL: str = ""  # Telegram Mini App URL (used in bot welcome message)
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Database (MySQL) ──────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # ── Telegram ──────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # ── Remnawave ─────────────────────────────────────────────────────────────
    REMNAWAVE_URL: str
    REMNAWAVE_API_KEY: str
    REMNAWAVE_WEBHOOK_SECRET: str = ""

    # ── Admin JWT ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── YooKassa ──────────────────────────────────────────────────────────────
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None

    # ── Referral ──────────────────────────────────────────────────────────────
    REFERRAL_CASHBACK_PERCENT: float = 10.0
    REFERRAL_MIN_WITHDRAWAL: float = 100.0

    # ── Trial ─────────────────────────────────────────────────────────────────
    TRIAL_ENABLED: bool = True
    TRIAL_DAYS: int = 3
    TRIAL_TRAFFIC_GB: Optional[float] = None  # None = unlimited

    # ── Notifications ─────────────────────────────────────────────────────────
    NOTIFY_SUBSCRIPTION_EXPIRY_DAYS: list[int] = [3, 1]
    NOTIFY_TRAFFIC_THRESHOLD_PERCENT: int = 80

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
