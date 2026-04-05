from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class ReferralStatsOut(BaseModel):
    referral_link: str
    total_invitees: int
    total_earned: Decimal
    pending_earned: Decimal
    cashback_percent: float


class ReferralRewardOut(BaseModel):
    id: int
    amount: Decimal
    is_credited: bool
    credited_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReferralRewardListOut(BaseModel):
    items: list[ReferralRewardOut]
    total: int
