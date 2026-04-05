import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserProfile
from app.services.wallet import wallet_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await wallet_service.get_or_create_wallet(user.id, db)
    result = UserProfile.model_validate(user)
    result.balance = float(wallet.balance)
    result.total_cashback_earned = float(wallet.total_cashback_earned)
    return result


@router.get("/me/referral-link")
async def get_referral_link(user: User = Depends(get_current_user)):
    bot_username = settings.TELEGRAM_BOT_TOKEN.split(":")[0]
    return {"referral_link": f"https://t.me/{bot_username}?start=ref_{user.id}"}


@router.get("/me/login-link")
async def get_login_link(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the user's personal auto-login link.
    Regenerates the token if it doesn't exist yet.
    Share this link to open the Mini App already authenticated.
    """
    if not user.login_token:
        user.login_token = secrets.token_urlsafe(16)
        await db.flush()
    return {
        "login_token": user.login_token,
        "login_url": f"{settings.APP_URL}/auth/t/{user.login_token}",
    }


@router.post("/me/login-link/regenerate")
async def regenerate_login_link(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidates the old token and generates a new one."""
    user.login_token = secrets.token_urlsafe(16)
    await db.flush()
    return {
        "login_token": user.login_token,
        "login_url": f"{settings.APP_URL}/auth/t/{user.login_token}",
    }
