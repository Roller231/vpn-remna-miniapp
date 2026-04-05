from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.subscription import SubscriptionStatus


class PlanOut(BaseModel):
    id: int
    product_id: int
    name: str
    duration_days: int
    devices: int
    price: Decimal
    discount_price: Optional[Decimal] = None
    price_stars: Optional[int] = None
    traffic_limit_gb: Optional[float] = None
    traffic_reset_days: Optional[int] = None
    traffic_reset_price: Optional[Decimal] = None
    is_trial: bool
    is_auto_renewal: bool

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    plans: list[PlanOut] = []

    model_config = {"from_attributes": True}


class SubscriptionOut(BaseModel):
    id: int
    plan: PlanOut
    status: SubscriptionStatus
    subscription_url: Optional[str] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    traffic_limit_bytes: Optional[int] = None
    traffic_used_bytes: int
    traffic_reset_at: Optional[datetime] = None
    devices_limit: int
    is_auto_renewal: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionCreate(BaseModel):
    plan_id: int
    pay_from_balance: bool = False


class SubscriptionRenew(BaseModel):
    subscription_id: int
    pay_from_balance: bool = False


class TrafficResetRequest(BaseModel):
    subscription_id: int
