import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://nothard_user@127.0.0.1/nothard"
    )

    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_ALG = "HS256"
    ACCESS_TTL = _int("ACCESS_TTL", 60 * 60 * 24 * 7)  # 7 days
    REFRESH_TTL = _int("REFRESH_TTL", 60 * 60 * 24 * 30)

    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://nothard.uz").rstrip("/")
    DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "ru")
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "https://nothard.uz,http://localhost:3000"
        ).split(",")
        if o.strip()
    ]

    # Telegram bot (Mini App initData validation + deep-link linking)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "notharduzbot")
    # URL the bot's Mini App button opens (the client cabinet, which auto-logins
    # via the signed Telegram initData).
    MINIAPP_URL = os.getenv("MINIAPP_URL", "").rstrip("/")

    # Telegram Login via OpenID Connect (BotFather → Web Login)
    TELEGRAM_OIDC_CLIENT_ID = os.getenv("TELEGRAM_OIDC_CLIENT_ID", "")
    TELEGRAM_OIDC_CLIENT_SECRET = os.getenv("TELEGRAM_OIDC_CLIENT_SECRET", "")
    TELEGRAM_OIDC_REDIRECT_URI = os.getenv(
        "TELEGRAM_OIDC_REDIRECT_URI", "https://nothard.uz/api/auth/telegram/callback"
    )


settings = Settings()

# Default the Mini App to the landing page (not the cabinet): the user sees the
# site first and explicitly chooses to sign in — via Telegram (initData) or email
# — instead of being auto-registered and dropped onto the consent screen.
if not settings.MINIAPP_URL:
    settings.MINIAPP_URL = f"{settings.FRONTEND_BASE_URL}/{settings.DEFAULT_LOCALE}"
