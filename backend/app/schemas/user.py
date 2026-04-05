from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.user import UserStatus


class UserBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None


class UserCreate(UserBase):
    id: int  # Telegram user ID
    language_code: Optional[str] = None
    referrer_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    status: UserStatus
    is_trial_used: bool
    registered_at: datetime
    balance: Optional[float] = None
    total_cashback_earned: Optional[float] = None

    model_config = {"from_attributes": True}


class UserProfile(UserOut):
    """Full profile returned to the Mini App."""
    pass


class UserUpdateStatus(BaseModel):
    status: UserStatus


class TelegramAuthData(BaseModel):
    """Raw initData string from Telegram WebApp."""
    init_data: str = Field(..., description="Raw initData string from Telegram.WebApp.initData")
