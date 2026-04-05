from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.referral import Referral, ReferralReward
from app.schemas.referral import ReferralStatsOut, ReferralRewardListOut, ReferralRewardOut
from app.services.referral import referral_service

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("/stats", response_model=ReferralStatsOut)
async def get_referral_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await referral_service.get_stats(user.id, db)
    bot_username = settings.TELEGRAM_BOT_USERNAME or settings.TELEGRAM_BOT_TOKEN.split(":")[0]
    return ReferralStatsOut(
        referral_link=f"https://t.me/{bot_username}?start=ref_{user.id}",
        **stats,
    )


@router.get("/rewards", response_model=ReferralRewardListOut)
async def get_referral_rewards(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    count_q = await db.execute(
        select(func.count(ReferralReward.id))
        .join(Referral, Referral.id == ReferralReward.referral_id)
        .where(Referral.referrer_id == user.id)
    )
    total = count_q.scalar_one()

    result = await db.execute(
        select(ReferralReward)
        .join(Referral, Referral.id == ReferralReward.referral_id)
        .where(Referral.referrer_id == user.id)
        .order_by(ReferralReward.created_at.desc())
        .offset(offset).limit(page_size)
    )
    items = list(result.scalars().all())
    return ReferralRewardListOut(
        items=[ReferralRewardOut.model_validate(r) for r in items],
        total=total,
    )
