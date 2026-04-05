"""
Subscription service — orchestrates plan purchase, renewal, and Remnawave sync.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.product import Plan
from app.models.wallet import TransactionType
from app.services.remnawave import remnawave_client, RemnawaveError
from app.services.wallet import wallet_service, InsufficientFundsError


class SubscriptionService:

    @staticmethod
    async def get_active_subscriptions(user_id: int, db: AsyncSession) -> list[Subscription]:
        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                ])
            )
            .order_by(Subscription.expires_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_plan(plan_id: int, db: AsyncSession) -> Plan:
        result = await db.execute(select(Plan).where(Plan.id == plan_id, Plan.is_active == True))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found or inactive")
        return plan

    @staticmethod
    async def purchase(
        user_id: int,
        plan_id: int,
        db: AsyncSession,
        pay_from_balance: bool = False,
        is_trial: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Subscription:
        plan = await SubscriptionService.get_plan(plan_id, db)
        price = plan.discount_price or plan.price

        # Deduct balance if requested
        if pay_from_balance and not is_trial:
            await wallet_service.debit(
                user_id=user_id,
                amount=price,
                tx_type=TransactionType.PURCHASE,
                db=db,
                description=f"Покупка подписки: {plan.name}",
                reference_id=f"plan_{plan_id}",
                idempotency_key=idempotency_key,
            )

        # Create Remnawave user
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=plan.duration_days)
        traffic_bytes = int(plan.traffic_limit_gb * 1024 ** 3) if plan.traffic_limit_gb else None

        remna_username = f"tg_{user_id}_{int(now.timestamp())}"
        try:
            remna_user = await remnawave_client.create_user(
                username=remna_username,
                traffic_limit_bytes=traffic_bytes,
                expire_at=expires_at,
                devices_limit=plan.devices,
            )
            remna_uuid = remna_user.get("uuid") or remna_user.get("data", {}).get("uuid")
            sub_url = remna_user.get("subscriptionUrl") or remna_user.get("data", {}).get("subscriptionUrl")
        except RemnawaveError as e:
            raise RuntimeError(f"Remnawave error: {e}") from e

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.TRIAL if is_trial else SubscriptionStatus.ACTIVE,
            remnawave_uuid=remna_uuid,
            subscription_url=sub_url,
            started_at=now,
            expires_at=expires_at,
            traffic_limit_bytes=traffic_bytes,
            traffic_used_bytes=0,
            devices_limit=plan.devices,
            is_auto_renewal=plan.is_auto_renewal,
        )
        db.add(subscription)
        await db.flush()
        return subscription

    @staticmethod
    async def renew(
        subscription_id: int,
        user_id: int,
        db: AsyncSession,
        pay_from_balance: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Subscription:
        result = await db.execute(
            select(Subscription).where(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id,
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError("Subscription not found")

        plan = await SubscriptionService.get_plan(sub.plan_id, db)
        price = plan.discount_price or plan.price

        if pay_from_balance:
            await wallet_service.debit(
                user_id=user_id,
                amount=price,
                tx_type=TransactionType.RENEWAL,
                db=db,
                description=f"Продление подписки: {plan.name}",
                reference_id=f"sub_{subscription_id}",
                idempotency_key=idempotency_key,
            )

        # Extend in Remnawave
        now = datetime.now(timezone.utc)
        base = max(sub.expires_at or now, now)
        new_expiry = base + timedelta(days=plan.duration_days)

        if sub.remnawave_uuid:
            try:
                await remnawave_client.update_user(
                    sub.remnawave_uuid,
                    expireAt=new_expiry.isoformat(),
                )
                await remnawave_client.enable_user(sub.remnawave_uuid)
            except RemnawaveError as e:
                raise RuntimeError(f"Remnawave error: {e}") from e

        sub.expires_at = new_expiry
        sub.status = SubscriptionStatus.ACTIVE
        sub.notify_3d_sent = False
        sub.notify_1d_sent = False
        await db.flush()
        return sub

    @staticmethod
    async def sync_from_remnawave(subscription: Subscription, db: AsyncSession) -> None:
        """Pull latest status/traffic from Remnawave and update local record."""
        if not subscription.remnawave_uuid:
            return
        try:
            data = await remnawave_client.get_user(subscription.remnawave_uuid)
            user_data = data.get("data", data)
            subscription.traffic_used_bytes = user_data.get("usedTrafficBytes", subscription.traffic_used_bytes)
            expire_str = user_data.get("expireAt")
            if expire_str:
                subscription.expires_at = datetime.fromisoformat(expire_str.rstrip("Z")).replace(tzinfo=timezone.utc)
            status_map = {
                "ACTIVE": SubscriptionStatus.ACTIVE,
                "DISABLED": SubscriptionStatus.DISABLED,
                "EXPIRED": SubscriptionStatus.EXPIRED,
            }
            remna_status = user_data.get("status", "")
            if remna_status in status_map:
                subscription.status = status_map[remna_status]
            await db.flush()
        except RemnawaveError:
            pass


    @staticmethod
    async def create_pending_for_payment(user_id: int, plan_id: int, db: AsyncSession) -> Subscription:
        """Creates a PENDING subscription (no Remnawave yet). Called before external payment."""
        plan = await SubscriptionService.get_plan(plan_id, db)
        sub = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.PENDING,
            devices_limit=plan.devices,
            is_auto_renewal=plan.is_auto_renewal,
        )
        db.add(sub)
        await db.flush()
        return sub

    @staticmethod
    async def activate_pending_subscription(subscription: Subscription, db: AsyncSession) -> Subscription:
        """Called on payment.succeeded — creates Remnawave user and activates the subscription."""
        plan = await SubscriptionService.get_plan(subscription.plan_id, db)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=plan.duration_days)
        traffic_bytes = int(plan.traffic_limit_gb * 1024 ** 3) if plan.traffic_limit_gb else None

        remna_username = f"tg_{subscription.user_id}_{int(now.timestamp())}"
        try:
            remna_user = await remnawave_client.create_user(
                username=remna_username,
                traffic_limit_bytes=traffic_bytes,
                expire_at=expires_at,
                devices_limit=plan.devices,
            )
            remna_uuid = remna_user.get("uuid") or remna_user.get("data", {}).get("uuid")
            sub_url = remna_user.get("subscriptionUrl") or remna_user.get("data", {}).get("subscriptionUrl")
        except RemnawaveError as e:
            raise RuntimeError(f"Remnawave error: {e}") from e

        subscription.remnawave_uuid = remna_uuid
        subscription.subscription_url = sub_url
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.started_at = now
        subscription.expires_at = expires_at
        subscription.traffic_limit_bytes = traffic_bytes
        subscription.traffic_used_bytes = 0
        await db.flush()
        return subscription


subscription_service = SubscriptionService()
