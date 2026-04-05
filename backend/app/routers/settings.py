"""
App settings router.
Public: GET /settings — returns all public key-value settings (bot texts, images, etc).
Admin: GET/PUT /admin/settings/{key} — manage individual settings.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.models.admin import AdminUser
from app.models.setting import AppSetting

router = APIRouter(tags=["settings"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SettingOut(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpsert(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("/settings", response_model=dict[str, Optional[str]])
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """
    Returns all public settings as a flat key→value dict.
    Used by the Mini App to load bot welcome text, images, etc.
    """
    result = await db.execute(
        select(AppSetting).where(AppSetting.is_public == True)
    )
    return {s.key: s.value for s in result.scalars().all()}


@router.get("/settings/{key}", response_model=SettingOut)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == key, AppSetting.is_public == True)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return SettingOut.model_validate(setting)


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/settings", response_model=list[SettingOut])
async def admin_list_settings(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all settings including private ones."""
    result = await db.execute(select(AppSetting).order_by(AppSetting.key))
    return [SettingOut.model_validate(s) for s in result.scalars().all()]


@router.put("/admin/settings/{key}", response_model=SettingOut)
async def admin_upsert_setting(
    key: str,
    body: SettingUpsert,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a setting by key."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = body.value
        if body.description is not None:
            setting.description = body.description
        setting.is_public = body.is_public
    else:
        setting = AppSetting(
            key=key,
            value=body.value,
            description=body.description,
            is_public=body.is_public,
        )
        db.add(setting)

    await db.flush()
    return SettingOut.model_validate(setting)


@router.delete("/admin/settings/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_setting(
    key: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    await db.delete(setting)
