from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.payment import PaymentStatus, PaymentMethodType


class PaymentOut(BaseModel):
    id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: PaymentMethodType
    description: Optional[str] = None
    is_topup: bool
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListOut(BaseModel):
    items: list[PaymentOut]
    total: int
    page: int
    page_size: int


class TopUpRequest(BaseModel):
    amount: Decimal
    method: PaymentMethodType = PaymentMethodType.YOOKASSA
    return_url: Optional[str] = None


class TopUpResponse(BaseModel):
    payment_id: int
    provider_payment_id: Optional[str] = None
    confirmation_url: Optional[str] = None
    status: PaymentStatus


class PaymentMethodOut(BaseModel):
    id: int
    method_type: PaymentMethodType
    title: Optional[str] = None
    is_default: bool

    model_config = {"from_attributes": True}
