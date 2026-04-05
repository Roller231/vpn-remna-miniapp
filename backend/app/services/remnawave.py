"""
Remnawave API client.
All interactions with the Remnawave panel go through this service.
Supported API version: v1 (as documented at https://remnawave.github.io/backend/)
"""
import httpx
from urllib.parse import urlparse, urlunparse, parse_qs
from typing import Optional, Any
from datetime import datetime
from app.config import settings


class RemnawaveError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class RemnawaveClient:
    def __init__(self):
        parsed = urlparse(settings.REMNAWAVE_URL)
        # Base URL without query string (used as httpx base_url)
        self._base_url = urlunparse(parsed._replace(query="", fragment="")).rstrip("/")
        # Query params extracted from URL (e.g. ?MWLaqjxy=hVnlDuqe) appended to every request
        self._url_params = {
            k: v[0] for k, v in parse_qs(parsed.query).items()
        }
        self._headers = {
            "Authorization": f"Bearer {settings.REMNAWAVE_API_KEY}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=30.0,
        )

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        # Merge URL params (from REMNAWAVE_URL query string) into every request
        if self._url_params:
            existing = kwargs.pop("params", {}) or {}
            kwargs["params"] = {**self._url_params, **existing}
        async with self._client() as client:
            response = await client.request(method, path, **kwargs)
            if response.status_code >= 400:
                raise RemnawaveError(
                    f"Remnawave API error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()

    # ── Users ─────────────────────────────────────────────────────────────────

    async def create_user(
        self,
        username: str,
        traffic_limit_bytes: Optional[int] = None,
        expire_at: Optional[datetime] = None,
        devices_limit: Optional[int] = None,
        inbound_uuids: Optional[list[str]] = None,
    ) -> dict:
        payload: dict[str, Any] = {"username": username}
        if traffic_limit_bytes is not None:
            payload["trafficLimitBytes"] = traffic_limit_bytes
        if expire_at is not None:
            payload["expireAt"] = expire_at.isoformat()
        if devices_limit is not None:
            payload["devicesLimit"] = devices_limit
        if inbound_uuids is not None:
            payload["inboundUuids"] = inbound_uuids
        return await self._request("POST", "/api/users", json=payload)

    async def get_user(self, uuid: str) -> dict:
        return await self._request("GET", f"/api/users/{uuid}")

    async def update_user(self, uuid: str, **fields) -> dict:
        return await self._request("PUT", f"/api/users/{uuid}", json=fields)

    async def delete_user(self, uuid: str) -> dict:
        return await self._request("DELETE", f"/api/users/{uuid}")

    async def disable_user(self, uuid: str) -> dict:
        return await self._request("POST", f"/api/users/{uuid}/disable")

    async def enable_user(self, uuid: str) -> dict:
        return await self._request("POST", f"/api/users/{uuid}/enable")

    async def reset_user_traffic(self, uuid: str) -> dict:
        return await self._request("POST", f"/api/users/{uuid}/reset-traffic")

    async def revoke_user_subscription(self, uuid: str) -> dict:
        return await self._request("POST", f"/api/users/{uuid}/revoke-subscription")

    async def get_user_subscription_info(self, uuid: str) -> dict:
        """Returns subscription URL and config links."""
        return await self._request("GET", f"/api/users/{uuid}/subscription")

    # ── Inbounds ──────────────────────────────────────────────────────────────

    async def list_inbounds(self) -> list[dict]:
        data = await self._request("GET", "/api/inbounds")
        return data if isinstance(data, list) else data.get("data", [])

    async def get_inbound(self, uuid: str) -> dict:
        return await self._request("GET", f"/api/inbounds/{uuid}")

    # ── Nodes ─────────────────────────────────────────────────────────────────

    async def list_nodes(self) -> list[dict]:
        data = await self._request("GET", "/api/nodes")
        return data if isinstance(data, list) else data.get("data", [])

    # ── System ────────────────────────────────────────────────────────────────

    async def get_system_stats(self) -> dict:
        return await self._request("GET", "/api/system/stats")

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/api/system/health")
            return True
        except RemnawaveError:
            return False


# Singleton
remnawave_client = RemnawaveClient()
