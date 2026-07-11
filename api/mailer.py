"""Minimal transactional email sender for verification codes.

Delivery backend, in order of preference:
  1. Resend HTTP API  — set RESEND_API_KEY (+ MAIL_FROM, a verified-domain sender).
  2. SMTP             — set MAIL_HOST/MAIL_PORT/MAIL_USER/MAIL_PASS/MAIL_FROM.
  3. Dev fallback     — logs the code (journalctl -u nothard-api2) so the flow still works.
"""

import json
import os
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage


def _cfg(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def email_configured() -> bool:
    """True if we can actually deliver (Resend or SMTP)."""
    if _cfg("RESEND_API_KEY") and _cfg("MAIL_FROM"):
        return True
    return bool(_cfg("MAIL_HOST") and _cfg("MAIL_FROM"))


def _send_resend(to: str, subject: str, body: str) -> bool:
    payload = json.dumps(
        {"from": _cfg("MAIL_FROM"), "to": [to], "subject": subject, "text": body}
    ).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {_cfg('RESEND_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200 <= r.status < 300
    except Exception as e:  # noqa: BLE001
        print(f"[mailer:resend ERROR] {to}: {e}", flush=True)
        return False


def send_code(to: str, code: str, subject: str = "Nothard — код подтверждения") -> bool:
    """Send a 6-digit verification code. Returns True if delivered (or logged in dev)."""
    body = (
        f"Ваш код подтверждения Nothard: {code}\n\n"
        f"Код действует 15 минут. Если вы не запрашивали его — просто игнорируйте это письмо.\n\n"
        f"Your Nothard verification code: {code} (valid for 15 minutes)."
    )

    if _cfg("RESEND_API_KEY") and _cfg("MAIL_FROM"):
        return _send_resend(to, subject, body)

    if not email_configured():
        # Dev fallback — visible in the API logs (journalctl -u nothard-api2).
        print(f"[mailer:DEV] code for {to}: {code}", flush=True)
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _cfg("MAIL_FROM")
    msg["To"] = to
    msg.set_content(body)

    host = _cfg("MAIL_HOST")
    port = int(_cfg("MAIL_PORT", "587") or "587")
    user = _cfg("MAIL_USER")
    password = _cfg("MAIL_PASS")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20) as s:
                if user:
                    s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=ssl.create_default_context())
                if user:
                    s.login(user, password)
                s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[mailer:ERROR] {to}: {e}", flush=True)
        return False
