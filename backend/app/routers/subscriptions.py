import uuid
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.payment import Payment, PaymentStatus, PaymentMethodType
from app.models.product import Product, Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import (
    ProductOut, PlanOut, SubscriptionOut, SubscriptionCreate, SubscriptionRenew, TrafficResetRequest
)
from app.services.subscription import subscription_service
from app.services.wallet import wallet_service, InsufficientFundsError
from app.services.yookassa import yookassa_service, YookassaError
from app.services.referral import referral_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/catalog", response_model=list[ProductOut])
async def get_catalog(db: AsyncSession = Depends(get_db)):
    """Public catalog of active products with their plans."""
    result = await db.execute(
        select(Product)
        .where(Product.is_active == True)
        .options(selectinload(Product.plans))
        .order_by(Product.sort_order)
    )
    products = list(result.scalars().all())
    return [ProductOut.model_validate(p) for p in products if p.plans]


@router.get("/my", response_model=list[SubscriptionOut])
async def get_my_subscriptions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active subscriptions for current user, synced from Remnawave."""
    subs = await subscription_service.get_active_subscriptions(user.id, db)
    for sub in subs:
        await subscription_service.sync_from_remnawave(sub, db)
    return [SubscriptionOut.model_validate(s) for s in subs]


@router.post("/purchase", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def purchase_subscription(
    body: SubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Purchase a new subscription, paying from balance."""
    if not body.pay_from_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only balance payments are supported here. Use /payments/topup first."
        )
    idempotency_key = f"purchase_{user.id}_{body.plan_id}_{uuid.uuid4().hex[:8]}"
    try:
        sub = await subscription_service.purchase(
            user_id=user.id,
            plan_id=body.plan_id,
            db=db,
            pay_from_balance=True,
            idempotency_key=idempotency_key,
        )
    except InsufficientFundsError:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient balance")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Award referral cashback for balance purchases
    try:
        plan_res = await db.execute(select(Plan).where(Plan.id == body.plan_id))
        plan_obj = plan_res.scalar_one_or_none()
        if plan_obj:
            price = plan_obj.discount_price or plan_obj.price
            await referral_service.award_cashback(
                payment_amount=price,
                invitee_id=user.id,
                db=db,
                duration_days=plan_obj.duration_days,
            )
    except Exception:
        pass

    return SubscriptionOut.model_validate(sub)


@router.post("/trial", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def activate_trial(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate trial subscription (one-time per user)."""
    if not settings.TRIAL_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not available")
    if user.is_trial_used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial already used")

    # Find trial plan
    result = await db.execute(select(Plan).where(Plan.is_trial == True, Plan.is_active == True).limit(1))
    trial_plan = result.scalar_one_or_none()
    if not trial_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trial plan configured")

    sub = await subscription_service.purchase(
        user_id=user.id,
        plan_id=trial_plan.id,
        db=db,
        pay_from_balance=False,
        is_trial=True,
    )
    user.is_trial_used = True
    return SubscriptionOut.model_validate(sub)


@router.post("/renew", response_model=SubscriptionOut)
async def renew_subscription(
    body: SubscriptionRenew,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Renew an existing subscription from balance."""
    idempotency_key = f"renew_{user.id}_{body.subscription_id}_{uuid.uuid4().hex[:8]}"
    try:
        sub = await subscription_service.renew(
            subscription_id=body.subscription_id,
            user_id=user.id,
            db=db,
            pay_from_balance=body.pay_from_balance,
            idempotency_key=idempotency_key,
        )
    except InsufficientFundsError:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient balance")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Award referral cashback for balance renewals
    if body.pay_from_balance:
        try:
            plan_res = await db.execute(select(Plan).where(Plan.id == sub.plan_id))
            plan_obj = plan_res.scalar_one_or_none()
            if plan_obj:
                price = plan_obj.discount_price or plan_obj.price
                await referral_service.award_cashback(
                    payment_amount=price,
                    invitee_id=user.id,
                    db=db,
                    duration_days=plan_obj.duration_days,
                )
        except Exception:
            pass

    return SubscriptionOut.model_validate(sub)


@router.post("/purchase-with-yookassa", status_code=status.HTTP_201_CREATED)
async def purchase_with_yookassa(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    return_url: Optional[str] = None,
):
    """
    Create a direct YooKassa payment for a subscription plan.
    Returns a payment_url to redirect the user to.
    On successful payment, the webhook activates the subscription.
    """
    plan_result = await db.execute(select(Plan).where(Plan.id == plan_id, Plan.is_active == True))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    price = plan.discount_price or plan.price
    redirect_url = return_url or settings.MINIAPP_URL or "https://t.me"

    # Create pending subscription (Remnawave activated on payment success)
    sub = await subscription_service.create_pending_for_payment(user.id, plan.id, db)

    idempotency_key = f"yk_sub_{user.id}_{sub.id}_{uuid.uuid4().hex[:8]}"
    payment = Payment(
        user_id=user.id,
        subscription_id=sub.id,
        amount=price,
        currency="RUB",
        status=PaymentStatus.PENDING,
        method=PaymentMethodType.YOOKASSA,
        idempotency_key=idempotency_key,
        is_topup=False,
        description=f"VPN подписка: {plan.name}",
    )
    db.add(payment)
    await db.flush()

    try:
        yk_payment = await yookassa_service.create_payment(
            amount=price,
            description=f"VPN подписка: {plan.name} ({plan.duration_days} дн.)",
            return_url=redirect_url,
            metadata={"payment_id": str(payment.id), "subscription_id": str(sub.id)},
            idempotency_key=idempotency_key,
        )
    except YookassaError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    payment.provider_payment_id = yk_payment["id"]
    payment.provider_meta = yk_payment
    await db.flush()

    return {
        "payment_url": yk_payment.get("confirmation", {}).get("confirmation_url"),
        "payment_id": payment.id,
        "subscription_id": sub.id,
        "plan": PlanOut.model_validate(plan),
    }


@router.post("/create-stars-invoice")
async def create_stars_invoice(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Telegram Stars invoice link via Bot API createInvoiceLink.
    Returns the invoice URL to pass to WebApp.openInvoice().
    """
    import httpx

    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.is_active == True)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan or not plan.price_stars:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or has no Stars price",
        )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/createInvoiceLink",
            json={
                "title": f"VPN: {plan.name}",
                "description": f"{plan.duration_days} дней, {plan.devices} устр.",
                "payload": f"plan_{plan.id}_user_{user.id}",
                "currency": "XTR",
                "prices": [{"label": plan.name, "amount": plan.price_stars}],
            },
        )

    data = resp.json()
    if not data.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram API error: {data.get('description', 'unknown')}",
        )

    return {"invoice_url": data["result"]}


@router.post("/toggle-auto-renewal/{subscription_id}")
async def toggle_auto_renewal(
    subscription_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    sub.is_auto_renewal = not sub.is_auto_renewal
    return {"is_auto_renewal": sub.is_auto_renewal}
