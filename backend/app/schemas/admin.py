from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.admin import AdminRole


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminUserOut(BaseModel):
    id: int
    username: str
    role: AdminRole
    is_active: bool
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    username: str
    password: str
    role: AdminRole = AdminRole.MODERATOR


class AdminAuditLogOut(BaseModel):
    id: int
    admin_username: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_users: int
    active_subscriptions: int
    expired_subscriptions: int
    revenue_today: float
    revenue_month: float
    pending_payments: int
    expiring_soon_count: int
    traffic_exhausted_count: int
