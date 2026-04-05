from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.wallet import TransactionType


class WalletOut(BaseModel):
    balance: Decimal
    total_cashback_earned: Decimal

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: int
    type: TransactionType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListOut(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class AdminBalanceAdjust(BaseModel):
    user_id: int
    amount: Decimal = Field(..., description="Positive = credit, negative = debit")
    description: Optional[str] = None
