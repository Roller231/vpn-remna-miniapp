"""
Admin API — protected by JWT admin tokens with RBAC.
"""
import uuid
from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, String, cast

from app.database import get_db
from app.core.dependencies import get_current_admin, require_role
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.admin import AdminUser, AdminRole, AdminAuditLog
from app.models.user import User, UserStatus
from app.models.wallet import TransactionType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.admin import (
    AdminLoginRequest, AdminTokenResponse, AdminUserOut, AdminUserCreate,
    AdminAuditLogOut, DashboardStats
)
from app.schemas.user import UserOut
from app.schemas.wallet import AdminBalanceAdjust
from app.schemas.subscription import ProductOut
from app.services.wallet import wallet_service, InsufficientFundsError
from app.services.remnawave import remnawave_client
from app.models.content import ContentPage
from app.models.product import Product, Plan

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.username == body.username))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account inactive")

    admin.last_login_at = datetime.now(timezone.utc)
    token_data = {"sub": str(admin.id), "type": "admin", "role": admin.role}
    return AdminTokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/register-first", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def register_first_admin(body: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    """Bootstrap first superadmin. Blocked if any admin already exists."""
    count = await db.execute(select(func.count()).select_from(AdminUser))
    if count.scalar_one() > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin already exists")
    admin = AdminUser(
        username=body.username,
        password_hash=hash_password(body.password),
        role=AdminRole.SUPERADMIN,
    )
    db.add(admin)
    await db.flush()
    return AdminUserOut.model_validate(admin)


@router.get("/me", response_model=AdminUserOut)
async def get_admin_me(admin: AdminUser = Depends(get_current_admin)):
    """Returns current admin profile. Use this to verify your admin token in Swagger."""
    return AdminUserOut.model_validate(admin)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_subs = (await db.execute(
        select(func.count()).where(Subscription.status == SubscriptionStatus.ACTIVE)
    )).scalar_one()
    expired_subs = (await db.execute(
        select(func.count()).where(Subscription.status == SubscriptionStatus.EXPIRED)
    )).scalar_one()

    from datetime import date, timedelta
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    month_start = datetime.combine(date.today().replace(day=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    revenue_today = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == PaymentStatus.SUCCEEDED, Payment.paid_at >= today_start)
    )).scalar_one()
    revenue_month = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == PaymentStatus.SUCCEEDED, Payment.paid_at >= month_start)
    )).scalar_one()
    pending_payments = (await db.execute(
        select(func.count()).where(Payment.status == PaymentStatus.PENDING)
    )).scalar_one()

    expiring_soon = (await db.execute(
        select(func.count()).where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at <= datetime.now(timezone.utc) + timedelta(days=3),
        )
    )).scalar_one()

    return DashboardStats(
        total_users=total_users,
        active_subscriptions=active_subs,
        expired_subscriptions=expired_subs,
        revenue_today=float(revenue_today),
        revenue_month=float(revenue_month),
        pending_payments=pending_payments,
        expiring_soon_count=expiring_soon,
        traffic_exhausted_count=0,
    )


# ── Users management ──────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut])
async def list_users(
    search: str = "",
    page: int = 1,
    page_size: int = 50,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    q = select(User)
    if search:
        q = q.where(
            (User.username.ilike(f"%{search}%")) |
            (cast(User.id, String).ilike(f"%{search}%")) |
            (User.first_name.ilike(f"%{search}%"))
        )
    result = await db.execute(q.order_by(User.registered_at.desc()).offset(offset).limit(page_size))
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.status = UserStatus.BANNED
    _audit(admin, "ban_user", "user", str(user_id), db, request)
    return {"status": "banned"}


@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.status = UserStatus.ACTIVE
    _audit(admin, "unban_user", "user", str(user_id), db, request)
    return {"status": "active"}


@router.post("/wallet/adjust")
async def adjust_balance(
    body: AdminBalanceAdjust,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually credit or debit a user's balance."""
    idem_key = f"admin_adjust_{admin.id}_{body.user_id}_{uuid.uuid4().hex}"
    if body.amount > 0:
        tx = await wallet_service.credit(
            user_id=body.user_id,
            amount=body.amount,
            tx_type=TransactionType.ADMIN_CREDIT,
            db=db,
            description=body.description or f"Ручное начисление от {admin.username}",
            idempotency_key=idem_key,
        )
    else:
        try:
            tx = await wallet_service.debit(
                user_id=body.user_id,
                amount=abs(body.amount),
                tx_type=TransactionType.ADMIN_DEBIT,
                db=db,
                description=body.description or f"Ручное списание от {admin.username}",
                idempotency_key=idem_key,
            )
        except InsufficientFundsError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    _audit(admin, "adjust_balance", "user", str(body.user_id), db, request, {"amount": str(body.amount)})
    return {"transaction_id": tx.id, "balance_after": str(tx.balance_after)}


# ── Remnawave status ──────────────────────────────────────────────────────────

@router.get("/remnawave/health")
async def remnawave_health(admin: AdminUser = Depends(get_current_admin)):
    healthy = await remnawave_client.health_check()
    return {"connected": healthy}


@router.get("/audit-log", response_model=list[AdminAuditLogOut])
async def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    admin: AdminUser = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .offset(offset).limit(page_size)
    )
    return [AdminAuditLogOut.model_validate(r) for r in result.scalars().all()]


# ── Content (CMS) ────────────────────────────────────────────────────────────

class ContentPageIn(BaseModel):
    key: str
    title: str
    body: str
    is_active: bool = True


@router.get("/content", tags=["admin-content"])
async def list_content_pages(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ContentPage).order_by(ContentPage.key))
    return [{"key": p.key, "title": p.title, "is_active": p.is_active} for p in result.scalars().all()]


@router.put("/content/{key}", tags=["admin-content"])
async def upsert_content_page(
    key: str,
    body: ContentPageIn,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ContentPage).where(ContentPage.key == key))
    page = result.scalar_one_or_none()
    if page:
        page.title = body.title
        page.body = body.body
        page.is_active = body.is_active
    else:
        page = ContentPage(key=key, title=body.title, body=body.body, is_active=body.is_active)
        db.add(page)
    await db.flush()
    return {"key": page.key, "title": page.title}


# ── Products & Plans ──────────────────────────────────────────────────────────

@router.get("/products", tags=["admin-products"])
async def list_products(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).order_by(Product.sort_order))
    return [ProductOut.model_validate(p) for p in result.scalars().all()]


@router.post("/products", status_code=201, tags=["admin-products"])
async def create_product(
    name: str,
    description: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    product = Product(name=name, description=description or None)
    db.add(product)
    await db.flush()
    return {"id": product.id, "name": product.name}


@router.patch("/products/{product_id}", tags=["admin-products"])
async def toggle_product(
    product_id: int,
    is_active: bool,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = is_active
    return {"id": product.id, "is_active": product.is_active}


# ── Helper ────────────────────────────────────────────────────────────────────

def _audit(
    admin: AdminUser,
    action: str,
    target_type: str,
    target_id: str,
    db: AsyncSession,
    request: Request,
    details: dict | None = None,
):
    log = AdminAuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
