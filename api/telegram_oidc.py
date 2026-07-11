"""Login with Telegram via OpenID Connect (Authorization Code + PKCE).

Mirrors the flow used in /var/www/assista. Requires a Web Login registration
in @BotFather (Client ID + Client Secret + allowed redirect URI).

Endpoints:
  authorization: https://oauth.telegram.org/auth
  token:         https://oauth.telegram.org/token
  jwks:          https://oauth.telegram.org/.well-known/jwks.json
"""

import base64
import hashlib
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import requests
from jose import jwt

from config import settings

ISSUER = "https://oauth.telegram.org"
AUTH_ENDPOINT = "https://oauth.telegram.org/auth"
TOKEN_ENDPOINT = "https://oauth.telegram.org/token"
JWKS_URI = "https://oauth.telegram.org/.well-known/jwks.json"
SCOPE = "openid profile"

STATE_TTL = 600
TICKET_TTL = 120
JWKS_TTL = 3600

_states: dict[str, dict] = {}
_tickets: dict[str, dict] = {}
_jwks: dict = {"keys": None, "exp": 0.0}


def is_configured() -> bool:
    return bool(settings.TELEGRAM_OIDC_CLIENT_ID and settings.TELEGRAM_OIDC_CLIENT_SECRET)


def _now() -> float:
    return time.time()


def _prune() -> None:
    now = _now()
    for store in (_states, _tickets):
        for key in [k for k, v in store.items() if v["exp"] < now]:
            store.pop(key, None)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def create_authorization_url(mode: str, user_id: Optional[int]) -> str:
    _prune()
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(48)
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    _states[state] = {
        "verifier": verifier,
        "mode": mode,
        "user_id": user_id,
        "exp": _now() + STATE_TTL,
    }
    query = urlencode(
        {
            "client_id": settings.TELEGRAM_OIDC_CLIENT_ID,
            "redirect_uri": settings.TELEGRAM_OIDC_REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPE,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTH_ENDPOINT}?{query}"


def pop_state(state: str) -> Optional[dict]:
    _prune()
    return _states.pop(state, None)


def _get_jwks() -> dict:
    if _jwks["keys"] and _jwks["exp"] > _now():
        return _jwks["keys"]
    resp = requests.get(JWKS_URI, timeout=10)
    resp.raise_for_status()
    _jwks["keys"] = resp.json()
    _jwks["exp"] = _now() + JWKS_TTL
    return _jwks["keys"]


def exchange_code(code: str, verifier: str) -> str:
    creds = base64.b64encode(
        f"{settings.TELEGRAM_OIDC_CLIENT_ID}:{settings.TELEGRAM_OIDC_CLIENT_SECRET}".encode()
    ).decode()
    resp = requests.post(
        TOKEN_ENDPOINT,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.TELEGRAM_OIDC_REDIRECT_URI,
            "client_id": settings.TELEGRAM_OIDC_CLIENT_ID,
            "code_verifier": verifier,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise ValueError(f"token exchange failed: {resp.status_code} {resp.text[:300]}")
    id_token = resp.json().get("id_token")
    if not id_token:
        raise ValueError("token response had no id_token")
    return id_token


def validate_id_token(id_token: str) -> dict:
    jwks = _get_jwks()
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise ValueError("signing key not found in JWKS")
    alg = key.get("alg", "RS256")
    return jwt.decode(
        id_token,
        key,
        algorithms=[alg],
        audience=settings.TELEGRAM_OIDC_CLIENT_ID,
        issuer=ISSUER,
        options={"verify_at_hash": False},
    )


def store_ticket(access: str, refresh: str, role: str) -> str:
    _prune()
    ticket = secrets.token_urlsafe(24)
    _tickets[ticket] = {"access": access, "refresh": refresh, "role": role, "exp": _now() + TICKET_TTL}
    return ticket


def pop_ticket(ticket: str) -> Optional[dict]:
    _prune()
    return _tickets.pop(ticket, None)
