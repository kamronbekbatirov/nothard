import time
import bcrypt
import jwt

from config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def make_access_token(user_id: int, sid: int | None = None) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "type": "access", "iat": now, "exp": now + settings.ACCESS_TTL}
    if sid is not None:
        payload["sid"] = sid  # bind the token to a revocable Session row
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def make_refresh_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "type": "refresh", "iat": now, "exp": now + settings.REFRESH_TTL}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except jwt.PyJWTError:
        return None


def parse_user_agent(ua: str) -> dict:
    """Best-effort, dependency-free parse of a User-Agent string into a
    human-readable {browser, os, device}. Not exhaustive — just enough to show
    the user which of their devices a session belongs to."""
    ua = ua or ""
    low = ua.lower()

    # Operating system
    if "android" in low:
        os_name = "Android"
    elif any(k in low for k in ("iphone", "ipad", "ipod")):
        os_name = "iOS"
    elif "windows" in low:
        os_name = "Windows"
    elif "mac os x" in low or "macintosh" in low:
        os_name = "macOS"
    elif "cros" in low:
        os_name = "ChromeOS"
    elif "linux" in low:
        os_name = "Linux"
    else:
        os_name = "Unknown"

    # Browser (order matters — Telegram's WebView UA also contains Chrome/Safari;
    # Edge/Opera contain Chrome; Chrome contains Safari).
    if "telegram" in low:
        browser = "Telegram"
    elif "edg/" in low or "edga/" in low or "edgios/" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "firefox" in low or "fxios" in low:
        browser = "Firefox"
    elif "chrome" in low or "crios" in low:
        browser = "Chrome"
    elif "safari" in low:
        browser = "Safari"
    else:
        browser = "Browser"

    # Form factor
    if "ipad" in low or ("android" in low and "mobile" not in low) or "tablet" in low:
        device = "Tablet"
    elif any(k in low for k in ("mobi", "iphone", "ipod", "android")):
        device = "Mobile"
    else:
        device = "Desktop"

    return {"browser": browser, "os": os_name, "device": device}
