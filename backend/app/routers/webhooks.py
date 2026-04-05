"""
Webhook handlers for Remnawave and YooKassa events.
All events are logged to webhook_events_log for auditability and idempotency.
"""
import hmac
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.webhook import WebhookEventLog, WebhookSource
from app.models.payment import Payment, PaymentStatus
from app.models.product import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.wallet import TransactionType
from app.services.wallet import wallet_service
from app.services.referral import referral_service
from app.services.subscription import subscription_service
from app.services.notification import notification_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _log_event(
    source: WebhookSource,
    event_type: str,
    payload: dict,
    external_id: str | None,
    db: AsyncSession,
) -> WebhookEventLog:
    # Idempotency — skip duplicate events
    if external_id:
        existing = await db.execute(
            select(WebhookEventLog).where(
                WebhookEventLog.source == source,
                WebhookEventLog.external_id == external_id,
                WebhookEventLog.is_processed == True,
            )
        )
        if existing.scalar_one_or_none():
            return None  # type: ignore

    log = WebhookEventLog(
        source=source,
        event_type=event_type,
        external_id=external_id,
        payload=payload,
        is_processed=False,
    )
    db.add(log)
    await db.flush()
    return log


@router.post("/yookassa")
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """YooKassa sends payment status updates here."""
    body = await request.json()
    event_type: str = body.get("event", "")
    obj: dict = body.get("object", {})
    provider_payment_id: str = obj.get("id", "")

    log = await _log_event(
        WebhookSource.YOOKASSA,
        event_type,
        body,
        provider_payment_id,
        db,
    )
    if log is None:
        return {"status": "duplicate"}

    if event_type == "payment.succeeded":
        result = await db.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment and payment.status != PaymentStatus.SUCCEEDED:
            payment.status = PaymentStatus.SUCCEEDED
            payment.paid_at = datetime.now(timezone.utc)

            if payment.is_topup:
                # Credit wallet
                await wallet_service.credit(
                    user_id=payment.user_id,
                    amount=payment.amount,
                    tx_type=TransactionType.DEPOSIT,
                    db=db,
                    description=f"Пополнение баланса (платёж #{payment.id})",
                    reference_id=f"payment_{payment.id}",
                    idempotency_key=f"yk_topup_{payment.id}",
                )
                await notification_service.send_message(
                    chat_id=payment.user_id,
                    text=f"✅ Баланс пополнен на <b>{payment.amount} ₽</b>",
                )
            else:
                # Direct subscription payment — activate pending subscription in Remnawave
                duration_days = 30
                if payment.subscription_id:
                    sub_result = await db.execute(
                        select(Subscription).where(Subscription.id == payment.subscription_id)
                    )
                    pending_sub = sub_result.scalar_one_or_none()
                    if pending_sub and pending_sub.status == SubscriptionStatus.PENDING:
                        try:
                            pending_sub = await subscription_service.activate_pending_subscription(pending_sub, db)
                            await notification_service.send_message(
                                chat_id=payment.user_id,
                                text=f"✅ Подписка активирована! Ваша ссылка готова.",
                            )
                        except Exception:
                            pass
                    # Get plan duration for referral calculation
                    plan_result = await db.execute(
                        select(Plan).where(Plan.id == pending_sub.plan_id)
                    ) if pending_sub else None
                    if plan_result:
                        plan = plan_result.scalar_one_or_none()
                        duration_days = plan.duration_days if plan else 30

                # Award referral cashback scaled by subscription duration
                await referral_service.award_cashback(
                    payment_amount=payment.amount,
                    payment_id=payment.id,
                    invitee_id=payment.user_id,
                    db=db,
                    duration_days=duration_days,
                )

    elif event_type == "payment.canceled":
        result = await db.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.CANCELLED

    log.is_processed = True
    log.processed_at = datetime.now(timezone.utc)
    return {"status": "ok"}


@router.post("/remnawave")
async def remnawave_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Remnawave sends subscription lifecycle events here."""
    # Verify signature if configured
    if settings.REMNAWAVE_WEBHOOK_SECRET:
        sig = request.headers.get("X-Remnawave-Signature", "")
        raw = await request.body()
        expected = hmac.new(
            settings.REMNAWAVE_WEBHOOK_SECRET.encode(),
            raw,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    body = await request.json()
    event_type: str = body.get("event", "")
    obj: dict = body.get("data", {})
    external_id: str = obj.get("uuid", "")

    log = await _log_event(WebhookSource.REMNAWAVE, event_type, body, external_id, db)
    if log is None:
        return {"status": "duplicate"}

    # Find local subscription by remnawave UUID
    result = await db.execute(
        select(Subscription).where(Subscription.remnawave_uuid == external_id)
    )
    sub = result.scalar_one_or_none()

    if sub:
        if event_type in ("user.expired", "subscription.expired"):
            sub.status = SubscriptionStatus.EXPIRED
            await notification_service.send_message(
                chat_id=sub.user_id,
                text="⚠️ Ваша подписка <b>истекла</b>. Продлите её, чтобы продолжить пользоваться VPN.",
            )

        elif event_type in ("user.disabled", "subscription.disabled"):
            sub.status = SubscriptionStatus.DISABLED

        elif event_type in ("user.enabled", "subscription.enabled"):
            sub.status = SubscriptionStatus.ACTIVE

        elif event_type == "user.traffic_reset":
            sub.traffic_used_bytes = 0
            sub.traffic_reset_at = datetime.now(timezone.utc)
            sub.notify_traffic_sent = False

        elif event_type == "user.traffic_exceeded":
            sub.notify_traffic_sent = True
            await notification_service.send_message(
                chat_id=sub.user_id,
                text="⚠️ Трафик по подписке <b>исчерпан</b>. Доступ может быть ограничен.",
            )

    log.is_processed = True
    log.processed_at = datetime.now(timezone.utc)
    return {"status": "ok"}
