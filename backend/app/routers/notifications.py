"""
Admin notification / broadcast router.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.models.admin import AdminUser, AdminRole
from app.models.user import User, UserStatus
from app.models.notification import NotificationTemplate, NotificationJob, NotificationStatus
from app.services.notification import notification_service

router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class BroadcastRequest(BaseModel):
    text: str
    buttons: Optional[dict] = None
    user_ids: Optional[list[int]] = None  # None = all active users


class SingleNotifyRequest(BaseModel):
    user_id: int
    text: str
    buttons: Optional[dict] = None


class TemplateCreate(BaseModel):
    key: str
    name: str
    text: str
    buttons: Optional[dict] = None


class TemplateOut(BaseModel):
    id: int
    key: str
    name: str
    text: str
    buttons: Optional[dict] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/broadcast", status_code=status.HTTP_202_ACCEPTED)
async def broadcast(
    body: BroadcastRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enqueue a message to a segment or all active users."""
    if body.user_ids:
        target_ids = body.user_ids
    else:
        result = await db.execute(
            select(User.id).where(
                User.status == UserStatus.ACTIVE,
                User.is_bot_blocked == False,
            )
        )
        target_ids = [row[0] for row in result.fetchall()]

    for user_id in target_ids:
        await notification_service.enqueue(
            user_id=user_id,
            text=body.text,
            db=db,
            buttons=body.buttons,
        )

    return {"queued": len(target_ids)}


@router.post("/send-one", status_code=status.HTTP_200_OK)
async def send_to_user(
    body: SingleNotifyRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Send an immediate message to a single user."""
    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    success = await notification_service.send_message(
        chat_id=body.user_id,
        text=body.text,
        reply_markup=body.buttons,
    )
    return {"sent": success}


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.key))
    return [TemplateOut.model_validate(t) for t in result.scalars().all()]


@router.post("/templates", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.key == body.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template key already exists")

    tmpl = NotificationTemplate(**body.model_dump())
    db.add(tmpl)
    await db.flush()
    return TemplateOut.model_validate(tmpl)


@router.put("/templates/{key}", response_model=TemplateOut)
async def update_template(
    key: str,
    body: TemplateCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.key == key)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    tmpl.name = body.name
    tmpl.text = body.text
    tmpl.buttons = body.buttons
    await db.flush()
    return TemplateOut.model_validate(tmpl)
