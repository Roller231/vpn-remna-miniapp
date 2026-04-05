import hashlib
import hmac
import json
from urllib.parse import unquote, parse_qsl
from datetime import datetime, timezone
from typing import Optional

from app.config import settings


class TelegramAuthError(Exception):
    pass


def validate_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256.
    Returns parsed user dict if valid, raises TelegramAuthError otherwise.

    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    params = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("Missing hash in init_data")

    # Check freshness
    auth_date = params.get("auth_date")
    if auth_date:
        timestamp = int(auth_date)
        age = datetime.now(timezone.utc).timestamp() - timestamp
        if age > max_age_seconds:
            raise TelegramAuthError("init_data is expired")

    # Build data-check string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # Secret key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    # Expected hash
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise TelegramAuthError("Hash mismatch — invalid init_data")

    # Parse user JSON
    user_raw = params.get("user")
    if not user_raw:
        raise TelegramAuthError("No user field in init_data")

    try:
        user = json.loads(unquote(user_raw))
    except (json.JSONDecodeError, Exception):
        raise TelegramAuthError("Failed to parse user JSON")

    return user


def extract_referrer_id(start_param: Optional[str]) -> Optional[int]:
    """Extract referrer Telegram ID from start_param (e.g. 'ref_12345678')."""
    if not start_param:
        return None
    if start_param.startswith("ref_"):
        try:
            return int(start_param[4:])
        except ValueError:
            return None
    return None
