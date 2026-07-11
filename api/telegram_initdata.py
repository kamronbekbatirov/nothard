"""Validate Telegram Mini App initData (HMAC-SHA256 with the bot token).

See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from config import settings

MAX_AGE = 60 * 60 * 24  # accept initData up to 24h old


def validate_init_data(init_data: str, max_age: int = MAX_AGE) -> dict | None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not init_data:
        return None

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        return None

    try:
        auth_date = int(pairs.get("auth_date", "0"))
        if auth_date and (time.time() - auth_date) > max_age:
            return None
    except ValueError:
        return None

    user = pairs.get("user")
    if user:
        try:
            pairs["user"] = json.loads(user)
        except json.JSONDecodeError:
            pairs["user"] = None
    return pairs
