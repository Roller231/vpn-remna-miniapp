"""
Telegram Bot — VPN Remna
Handles: /start (with referral), welcome message, Mini App button, Telegram Stars payments.

Run: python -m bot.main
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    LabeledPrice, PreCheckoutQuery, SuccessfulPayment,
)
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select

from app.config import settings
from app.database import engine, get_db
from app.models.user import User, UserStatus
from app.models.wallet import Wallet
from app.models.referral import Referral
from app.models.product import Plan
from app.models.payment import Payment, PaymentStatus, PaymentMethodType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.setting import AppSetting
from app.services.subscription import subscription_service
from app.services.referral import referral_service
import uuid

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

router = Router()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_setting(key: str, default: str, db) -> str:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    s = result.scalar_one_or_none()
    return (s.value or default) if s else default


async def _upsert_user(tg_user, referrer_id: int | None, db) -> User:
    result = await db.execute(select(User).where(User.id == tg_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=tg_user.id,
            first_name=tg_user.first_name or "",
            last_name=tg_user.last_name,
            username=tg_user.username,
            language_code=tg_user.language_code,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        await db.flush()

        wallet = Wallet(user_id=tg_user.id)
        db.add(wallet)
        await db.flush()

        if referrer_id and referrer_id != tg_user.id:
            ref_exists = await db.execute(select(User).where(User.id == referrer_id))
            if ref_exists.scalar_one_or_none():
                db.add(Referral(referrer_id=referrer_id, invitee_id=tg_user.id))
                await db.flush()
    else:
        user.first_name = tg_user.first_name or user.first_name
        user.last_name = tg_user.last_name or user.last_name
        user.username = tg_user.username or user.username
        user.is_bot_blocked = False

    await db.commit()
    await db.refresh(user)
    return user


def _parse_referrer(arg: str | None) -> int | None:
    if arg and arg.startswith("ref_"):
        try:
            return int(arg[4:])
        except ValueError:
            pass
    return None


def _build_welcome_keyboard(button_text: str, miniapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=button_text,
            web_app=WebAppInfo(url=miniapp_url),
        )
    ]])


# ── /start handler ────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    referrer_id = _parse_referrer(command.args)

    async for db in get_db():
        await _upsert_user(message.from_user, referrer_id, db)

        welcome_text = await _get_setting(
            "bot_welcome_text",
            "👋 Добро пожаловать! Нажми кнопку ниже.",
            db,
        )
        button_text = await _get_setting(
            "bot_welcome_button_text",
            "🚀 Открыть приложение",
            db,
        )
        image_url = await _get_setting("bot_welcome_image_url", "", db)

    miniapp_url = settings.MINIAPP_URL or "https://t.me"
    keyboard = _build_welcome_keyboard(button_text, miniapp_url)

    if image_url:
        await message.answer_photo(
            photo=image_url,
            caption=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    else:
        await message.answer(
            text=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


# ── Telegram Stars payment ─────────────────────────────────────────────────────

@router.message(F.text.startswith("/buy_stars_"))
async def cmd_buy_stars(message: Message):
    """
    /buy_stars_{plan_id} — send Stars invoice for a plan.
    In production this is triggered from the Mini App via bot.openInvoice().
    """
    try:
        plan_id = int(message.text.split("_")[-1])
    except (ValueError, IndexError):
        await message.answer("Неверный план.")
        return

    async for db in get_db():
        result = await db.execute(
            select(Plan).where(Plan.id == plan_id, Plan.is_active == True)
        )
        plan = result.scalar_one_or_none()

    if not plan or not plan.price_stars:
        await message.answer("Этот план недоступен для оплаты Stars.")
        return

    await message.answer_invoice(
        title=f"VPN подписка: {plan.name}",
        description=f"{plan.duration_days} дней, {plan.devices} устройств",
        payload=f"plan_{plan.id}_user_{message.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=plan.name, amount=plan.price_stars)],
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    """Always approve pre-checkout for Stars."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_stars_payment(message: Message):
    """Activate subscription after Stars payment."""
    payment_info: SuccessfulPayment = message.successful_payment
    payload = payment_info.invoice_payload  # e.g. "plan_3_user_123456789"

    try:
        parts = payload.split("_")
        plan_id = int(parts[1])
        user_id = int(parts[3])
    except (IndexError, ValueError):
        logger.error("Invalid Stars payment payload: %s", payload)
        return

    async for db in get_db():
        # Create pending sub and activate immediately
        try:
            sub = await subscription_service.create_pending_for_payment(user_id, plan_id, db)
            sub = await subscription_service.activate_pending_subscription(sub, db)

            # Record the Stars payment
            stars_payment = Payment(
                user_id=user_id,
                subscription_id=sub.id,
                amount=0,
                currency="XTR",
                status=PaymentStatus.SUCCEEDED,
                method=PaymentMethodType.TELEGRAM_STARS,
                idempotency_key=f"stars_{payment_info.telegram_payment_charge_id}",
                is_topup=False,
                description=f"Stars payment for plan {plan_id}",
                provider_payment_id=payment_info.telegram_payment_charge_id,
            )
            db.add(stars_payment)
            await db.flush()

            # Award referral
            plan_result = await db.execute(select(Plan).where(Plan.id == plan_id))
            plan = plan_result.scalar_one_or_none()
            if plan:
                from app.services.referral import referral_service as rs
                from decimal import Decimal
                await rs.award_cashback(
                    payment_amount=Decimal(str(plan.price or 0)),
                    payment_id=stars_payment.id,
                    invitee_id=user_id,
                    db=db,
                    duration_days=plan.duration_days,
                )

            await db.commit()

            await message.answer(
                "✅ Оплата прошла успешно! Ваша подписка активирована.\n"
                "Ссылка для подключения доступна в приложении.",
            )
        except Exception as e:
            logger.exception("Failed to activate Stars subscription: %s", e)
            await message.answer(
                "⚠️ Оплата получена, но произошла ошибка при активации. "
                "Обратитесь в поддержку с кодом: " + payment_info.telegram_payment_charge_id
            )


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting bot polling...")
    await dp.start_polling(bot, allowed_updates=["message", "pre_checkout_query"])


if __name__ == "__main__":
    asyncio.run(main())
