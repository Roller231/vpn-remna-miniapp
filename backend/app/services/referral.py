"""
Referral service — tracks referral chains and awards cashback.
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.referral import Referral, ReferralReward
from app.models.setting import AppSetting
from app.models.wallet import TransactionType
from app.services.wallet import wallet_service


class ReferralService:

    @staticmethod
    async def register_referral(invitee_id: int, referrer_id: int, db: AsyncSession) -> Optional[Referral]:
        """Link invitee to referrer. Idempotent — does nothing if already linked."""
        if invitee_id == referrer_id:
            return None
        existing = await db.execute(
            select(Referral).where(Referral.invitee_id == invitee_id)
        )
        if existing.scalar_one_or_none():
            return None

        referral = Referral(referrer_id=referrer_id, invitee_id=invitee_id)
        db.add(referral)
        await db.flush()
        return referral

    @staticmethod
    async def award_cashback(
        payment_amount: Decimal,
        payment_id: int,
        invitee_id: int,
        db: AsyncSession,
        duration_days: int = 30,
    ) -> Optional[ReferralReward]:
        """
        Award cashback to referrer when invitee makes a payment.
        Reward = payment_amount * (referral_percent_per_day / 100) * (duration_days / 30)
        i.e. the percentage scales linearly with subscription duration.
        """
        referral_result = await db.execute(
            select(Referral).where(Referral.invitee_id == invitee_id)
        )
        referral = referral_result.scalar_one_or_none()
        if not referral:
            return None

        # Read configurable rate from AppSettings; fallback to env var
        setting_result = await db.execute(
            select(AppSetting).where(AppSetting.key == "referral_percent_per_day")
        )
        setting = setting_result.scalar_one_or_none()
        try:
            percent_per_day = float(setting.value) if setting and setting.value else settings.REFERRAL_CASHBACK_PERCENT
        except (ValueError, TypeError):
            percent_per_day = settings.REFERRAL_CASHBACK_PERCENT

        # Scale reward by months: 30 days = 1x, 90 days = 3x, etc.
        months = Decimal(str(duration_days)) / Decimal("30")
        cashback_amount = (payment_amount * Decimal(str(percent_per_day / 100)) * months).quantize(Decimal("0.01"))

        reward = ReferralReward(
            referral_id=referral.id,
            payment_id=payment_id,
            amount=cashback_amount,
            is_credited=False,
        )
        db.add(reward)
        await db.flush()

        # Credit wallet immediately
        idempotency_key = f"referral_reward_{reward.id}"
        await wallet_service.credit(
            user_id=referral.referrer_id,
            amount=cashback_amount,
            tx_type=TransactionType.CASHBACK,
            db=db,
            description=f"Реферальный кэшбэк за платёж #{payment_id}",
            reference_id=f"reward_{reward.id}",
            idempotency_key=idempotency_key,
        )
        reward.is_credited = True
        reward.credited_at = datetime.now(timezone.utc)
        await db.flush()
        return reward

    @staticmethod
    async def get_stats(referrer_id: int, db: AsyncSession) -> dict:
        count_result = await db.execute(
            select(func.count()).where(Referral.referrer_id == referrer_id)
        )
        total_invitees = count_result.scalar_one()

        total_earned_result = await db.execute(
            select(func.coalesce(func.sum(ReferralReward.amount), 0))
            .join(Referral, Referral.id == ReferralReward.referral_id)
            .where(Referral.referrer_id == referrer_id, ReferralReward.is_credited == True)
        )
        total_earned = Decimal(str(total_earned_result.scalar_one()))

        pending_result = await db.execute(
            select(func.coalesce(func.sum(ReferralReward.amount), 0))
            .join(Referral, Referral.id == ReferralReward.referral_id)
            .where(Referral.referrer_id == referrer_id, ReferralReward.is_credited == False)
        )
        pending_earned = Decimal(str(pending_result.scalar_one()))

        return {
            "total_invitees": total_invitees,
            "total_earned": total_earned,
            "pending_earned": pending_earned,
            "cashback_percent": settings.REFERRAL_CASHBACK_PERCENT,
        }


referral_service = ReferralService()
