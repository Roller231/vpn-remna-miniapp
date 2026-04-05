"""
YooKassa payment service.
"""
import uuid
from decimal import Decimal
from typing import Optional
import httpx
from app.config import settings


class YookassaError(Exception):
    pass


class YookassaService:
    BASE_URL = "https://api.yookassa.ru/v3"

    def _auth(self):
        return (settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)

    async def create_payment(
        self,
        amount: Decimal,
        description: str,
        return_url: str,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            raise YookassaError("YooKassa is not configured")

        key = idempotency_key or str(uuid.uuid4())
        payload = {
            "amount": {"value": str(amount), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description,
        }
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                auth=self._auth(),
                headers={"Idempotence-Key": key},
            )
            if resp.status_code not in (200, 201):
                raise YookassaError(f"YooKassa error {resp.status_code}: {resp.text}")
            return resp.json()

    async def get_payment(self, payment_id: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.BASE_URL}/payments/{payment_id}",
                auth=self._auth(),
            )
            if resp.status_code != 200:
                raise YookassaError(f"YooKassa error {resp.status_code}: {resp.text}")
            return resp.json()

    async def cancel_payment(self, payment_id: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments/{payment_id}/cancel",
                json={},
                auth=self._auth(),
                headers={"Idempotence-Key": str(uuid.uuid4())},
            )
            if resp.status_code != 200:
                raise YookassaError(f"YooKassa error {resp.status_code}: {resp.text}")
            return resp.json()

    def verify_webhook_ip(self, ip: str) -> bool:
        """YooKassa sends webhooks from a fixed set of IPs."""
        allowed_prefixes = ("185.71.76.", "185.71.77.", "77.75.153.", "77.75.156.")
        return any(ip.startswith(p) for p in allowed_prefixes)


yookassa_service = YookassaService()
