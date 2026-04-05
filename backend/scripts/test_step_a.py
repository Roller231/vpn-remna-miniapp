"""
Quick smoke-test for Step A endpoints.
Run: .venv\Scripts\python scripts\test_step_a.py
"""
import asyncio
import sys
import os
import json
import hashlib
import hmac
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from app.config import settings

BASE = "http://localhost:8000/api/v1"

TEST_USER = {
    "id": 123456789,
    "first_name": "Test",
    "username": "testuser",
    "language_code": "ru",
}


def make_init_data(user: dict) -> str:
    auth_date = str(int(time.time()))
    user_json = json.dumps(user, ensure_ascii=False, separators=(",", ":"))
    params = {"auth_date": auth_date, "user": user_json}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(params)


async def run():
    async with httpx.AsyncClient(timeout=10) as c:

        print("\n=== 1. Public settings ===")
        r = await c.get(f"{BASE}/settings")
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
        s = r.json()
        print("  Keys:", list(s.keys()))
        print("  bot_welcome_text:", repr(s.get("bot_welcome_text", "")[:40]))
        print("  referral_percent_per_day:", s.get("referral_percent_per_day"))

        print("\n=== 2. Telegram auth -> login_token ===")
        init_data = make_init_data(TEST_USER)
        r = await c.post(f"{BASE}/auth/telegram", json={"init_data": init_data})
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
        auth = r.json()
        login_token = auth.get("login_token")
        access_token = auth.get("access_token")
        print("  access_token:", access_token[:30], "...")
        print("  login_token:", login_token)
        assert login_token, "login_token is empty!"

        print("\n=== 3. Auto-login via token ===")
        r = await c.get(f"{BASE}/auth/t/{login_token}")
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
        d = r.json()
        print("  user:", d["user"]["first_name"], d["user"].get("username"))
        print("  new access_token:", d["access_token"][:30], "...")
        print("  login_token stable:", d["login_token"] == login_token)

        print("\n=== 4. GET /users/me/login-link ===")
        r = await c.get(f"{BASE}/users/me/login-link",
                        headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
        lnk = r.json()
        print("  login_url:", lnk["login_url"])

        print("\n=== 5. Plan catalog has price_stars field ===")
        r = await c.get(f"{BASE}/subscriptions/catalog")
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
        catalog = r.json()
        print("  Products:", [p["name"] for p in catalog])
        if catalog:
            plans = catalog[0].get("plans", [])
            if plans:
                print("  Plan keys:", list(plans[0].keys()))
                assert "price_stars" in plans[0], "price_stars missing from PlanOut!"

        print("\n✅ All Step A tests passed!")


if __name__ == "__main__":
    asyncio.run(run())
