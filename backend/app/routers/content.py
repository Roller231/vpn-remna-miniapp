"""
Content / CMS router.
Public endpoint to fetch pages (FAQ, ToS, onboarding texts).
Admin write endpoints live in admin.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.content import ContentPage

router = APIRouter(prefix="/content", tags=["content"])


class ContentPageOut(BaseModel):
    key: str
    title: str
    body: str
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{key}", response_model=ContentPageOut)
async def get_page(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContentPage).where(ContentPage.key == key, ContentPage.is_active == True)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return ContentPageOut.model_validate(page)
