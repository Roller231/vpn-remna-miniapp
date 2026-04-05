from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.referral import Referral, ReferralReward
from app.schemas.referral import ReferralStatsOut, ReferralRewardListOut, ReferralRewardOut
from functools import lru_cache
import httpx
from app.services.referral import referral_service

router = APIRouter(prefix="/referrals", tags=["referrals"])


@lru_cache()
def _resolve_bot_username() -> str:
    username = (settings.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")
    if username:
        return username
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe")
            data = r.json()
            u = data.get("result", {}).get("username")
            if u:
                return u
    except Exception:
        pass
    return settings.TELEGRAM_BOT_TOKEN.split(":")[0]


@router.get("/stats", response_model=ReferralStatsOut)
async def get_referral_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await referral_service.get_stats(user.id, db)
    bot_username = _resolve_bot_username()
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
