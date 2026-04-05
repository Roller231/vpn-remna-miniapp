"""
Auth router — validates Telegram WebApp initData and issues JWT tokens.
"""
from urllib.parse import parse_qsl
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from app.database import get_db
from app.schemas.user import TelegramAuthData, UserOut
from app.models.user import User, UserStatus
from app.models.wallet import Wallet
from app.models.referral import Referral
from app.utils.telegram_auth import validate_init_data, TelegramAuthError, extract_referrer_id
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

TOKEN_LENGTH = 16  # URL-safe base64 chars (~12 bytes entropy)


@router.post("/telegram", summary="Authenticate via Telegram WebApp initData")
async def telegram_auth(body: TelegramAuthData, db: AsyncSession = Depends(get_db)):
    """
    Validates initData from Telegram.WebApp.initData.
    Creates user on first call (upsert). Returns JWT access + refresh tokens.
    """
    try:
        tg_user = validate_init_data(body.init_data)
    except TelegramAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    user_id: int = tg_user["id"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        # New user — create with wallet
        user = User(
            id=user_id,
            first_name=tg_user.get("first_name", ""),
            last_name=tg_user.get("last_name"),
            username=tg_user.get("username"),
            language_code=tg_user.get("language_code"),
            photo_url=tg_user.get("photo_url"),
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        await db.flush()

        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        await db.flush()

        # Handle referral from start_param
        params = dict(parse_qsl(body.init_data))
        start_param = params.get("start_param")
        referrer_id = extract_referrer_id(start_param)
        if referrer_id and referrer_id != user_id:
            referral_exists = await db.execute(
                select(User).where(User.id == referrer_id)
            )
            if referral_exists.scalar_one_or_none():
                ref = Referral(referrer_id=referrer_id, invitee_id=user_id)
                db.add(ref)
                await db.flush()
    else:
        # Update profile fields from latest initData
        user.first_name = tg_user.get("first_name", user.first_name)
        user.last_name = tg_user.get("last_name", user.last_name)
        user.username = tg_user.get("username", user.username)
        user.photo_url = tg_user.get("photo_url", user.photo_url)
        user.is_bot_blocked = False

        if user.status == UserStatus.BANNED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")

    token_data = {"sub": str(user_id), "type": "user"}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Generate login_token on first auth if not present
    if not user.login_token:
        user.login_token = secrets.token_urlsafe(TOKEN_LENGTH)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "login_token": user.login_token,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "photo_url": user.photo_url,
        },
    }


@router.get("/t/{token}", summary="Auto-login via short token")
async def token_login(token: str, db: AsyncSession = Depends(get_db)):
    """
    Exchange a short login_token for a JWT.
    Used for magic-link auto-login: https://your-domain.com/auth/t/Y2Wrrcp06vkFq36_
    The Mini App opens with ?tgWebAppStartParam=<token> or via direct link.
    """
    result = await db.execute(select(User).where(User.login_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")
    if user.status == UserStatus.BANNED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")

    token_data = {"sub": str(user.id), "type": "user"}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "login_token": user.login_token,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "photo_url": user.photo_url,
        },
    }
