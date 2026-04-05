"""
Генерирует валидный Telegram WebApp initData для локального тестирования.
Использование: python scripts/gen_test_initdata.py
"""
import hashlib
import hmac
import json
import time
import urllib.parse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings

# Тестовый пользователь — меняй на свой Telegram ID
TEST_USER = {
    "id": 123456789,
    "first_name": "Test",
    "last_name": "User",
    "username": "testuser",
    "language_code": "ru",
}

def generate_init_data(user: dict, start_param: str = "") -> str:
    auth_date = str(int(time.time()))
    user_json = json.dumps(user, ensure_ascii=False, separators=(",", ":"))

    params = {
        "auth_date": auth_date,
        "user": user_json,
    }
    if start_param:
        params["start_param"] = start_param

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    params["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return urllib.parse.urlencode(params)


if __name__ == "__main__":
    init_data = generate_init_data(TEST_USER)
    print("=== initData для тестирования ===")
    print(init_data)
    print()
    print("=== curl команда ===")
    print(f"""curl -X POST http://localhost:8000/api/v1/auth/telegram \\
  -H "Content-Type: application/json" \\
  -d '{{"init_data": "{init_data}"}}'""")
    print()
    print("=== С реферальной ссылкой (ref_987654321) ===")
    init_data_ref = generate_init_data(TEST_USER, start_param="ref_987654321")
    print(init_data_ref)
