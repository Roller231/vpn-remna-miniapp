"""
Notification service — sends Telegram messages to users via Bot API.
"""
import httpx
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.config import settings
from app.models.notification import NotificationJob, NotificationTemplate, NotificationStatus


class NotificationService:
    BASE_URL = "https://api.telegram.org/bot"

    @property
    def _api_url(self) -> str:
        return f"{self.BASE_URL}{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML",
    ) -> bool:
        payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self._api_url}/sendMessage", json=payload)
            return resp.status_code == 200

    async def send_from_template(
        self,
        user_id: int,
        template_key: str,
        context: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """Load template from DB and send, substituting {vars} from context."""
        if db is None:
            return False
        result = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.key == template_key,
                NotificationTemplate.is_active == True,
            )
        )
        tmpl = result.scalar_one_or_none()
        if not tmpl:
            return False

        text = tmpl.text
        if context:
            for k, v in context.items():
                text = text.replace(f"{{{k}}}", str(v))

        return await self.send_message(user_id, text, reply_markup=tmpl.buttons)

    async def enqueue(
        self,
        user_id: int,
        text: str,
        db: AsyncSession,
        buttons: Optional[dict] = None,
        template_key: Optional[str] = None,
    ) -> NotificationJob:
        job = NotificationJob(
            user_id=user_id,
            text=text,
            buttons=buttons,
            template_key=template_key,
        )
        db.add(job)
        await db.flush()
        return job

    async def process_pending(self, db: AsyncSession) -> int:
        """Process pending notification jobs. Returns count of sent notifications."""
        result = await db.execute(
            select(NotificationJob).where(
                NotificationJob.status == NotificationStatus.PENDING,
                NotificationJob.scheduled_at <= datetime.now(timezone.utc),
            ).limit(100)
        )
        jobs = list(result.scalars().all())
        sent_count = 0
        for job in jobs:
            success = await self.send_message(job.user_id, job.text or "", job.buttons)
            job.status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            job.sent_at = datetime.now(timezone.utc)
            sent_count += 1 if success else 0
        await db.flush()
        return sent_count


notification_service = NotificationService()
