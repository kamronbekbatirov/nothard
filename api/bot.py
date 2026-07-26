"""notharduz_bot — Telegram bot for Nothard.

Responsibilities:
  * /start                -> greet + a "Launch app" button that opens the
                             Telegram Mini App (the client cabinet).
  * /start link_<code>    -> attach this Telegram account to the web account
                             that generated <code> in its cabinet.
  * sets the chat menu button to launch the Mini App.

Runs as a long-polling worker. Shares the API's database (SQLAlchemy models),
so account linking is reflected immediately in the web app.
"""

import json
import time

import requests
from sqlalchemy import select

from config import settings
from db import SessionLocal, init_db
from models import User, PhoneShare

API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

TEXTS = {
    "welcome": (
        "Добро пожаловать в *Nothard* — релокация в Лондон «под ключ».\n\n"
        "Нажмите кнопку ниже, чтобы открыть личный кабинет: путь переезда, "
        "статусы, документы и связь с менеджером."
    ),
    "open_app": "Открыть кабинет",
    "linked": (
        "✅ Telegram привязан к вашему аккаунту.\n\n"
        "Теперь вы можете открывать личный кабинет прямо здесь."
    ),
    "link_bad": (
        "Ссылка привязки недействительна или устарела. "
        "Откройте кабинет на сайте и запросите привязку заново."
    ),
    "already": "Вы уже вошли. Откройте кабинет кнопкой ниже.",
    "phone_saved": (
        "✅ Номер телефона сохранён — он появится в анкете автоматически.\n\n"
        "Можно возвращаться в кабинет."
    ),
    "phone_bad": (
        "Не удалось сохранить номер. Откройте кабинет и введите его вручную."
    ),
    "phone_ask": (
        "Нажмите кнопку ниже, чтобы поделиться своим номером телефона — он "
        "автоматически подставится в форму на сайте."
    ),
    "phone_share_btn": "📱 Поделиться номером",
    "phone_share_saved": (
        "✅ Номер получен. Вернитесь на сайт — он подставится в форму автоматически."
    ),
}


def _launch_markup() -> dict:
    return {
        "inline_keyboard": [[{"text": TEXTS["open_app"], "web_app": {"url": settings.MINIAPP_URL}}]]
    }


def send_message(chat_id: int, text: str, markup: dict | None = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if markup:
        payload["reply_markup"] = json.dumps(markup)
    try:
        requests.post(f"{API}/sendMessage", json=payload, timeout=20)
    except Exception as e:
        print(f"send_message error: {e}")


def set_menu_button():
    """Make the chat menu button launch the Mini App for everyone."""
    try:
        requests.post(
            f"{API}/setChatMenuButton",
            json={
                "menu_button": {
                    "type": "web_app",
                    "text": TEXTS["open_app"],
                    "web_app": {"url": settings.MINIAPP_URL},
                }
            },
            timeout=15,
        )
    except Exception as e:
        print(f"set_menu_button error: {e}")


def _contact_markup() -> dict:
    """A one-tap reply keyboard that asks the user to share their phone number."""
    return {
        "keyboard": [[{"text": TEXTS["phone_share_btn"], "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def _claim_phone_code(code: str, frm: dict) -> None:
    """Bind a pending phone-share code to this Telegram user, so their next shared
    contact fills it. Ignores unknown/expired codes."""
    row = SessionLocal.execute(
        select(PhoneShare).where(PhoneShare.code == code, PhoneShare.phone.is_(None))
    ).scalar_one_or_none()
    if row:
        row.tg_id = str(frm.get("id"))
        SessionLocal.commit()
    SessionLocal.remove()


def _link_account(code: str, frm: dict) -> bool:
    tg_id = str(frm.get("id"))
    username = frm.get("username")
    user = SessionLocal.execute(select(User).where(User.tg_link_code == code)).scalar_one_or_none()
    if not user:
        SessionLocal.remove()
        return False
    # Detach this Telegram id from any other account first.
    other = SessionLocal.execute(select(User).where(User.telegram_id == tg_id)).scalar_one_or_none()
    if other and other.id != user.id:
        other.telegram_id = None
        other.telegram_username = None
    user.telegram_id = tg_id
    user.telegram_username = username
    user.tg_link_code = None
    SessionLocal.commit()
    SessionLocal.remove()
    return True


def _clean_contact_phone(contact: dict, frm: dict) -> str | None:
    """Validate a shared contact is the sender's OWN card and return the number
    (never trust a forwarded contact — it could overwrite someone else's phone)."""
    sender = frm.get("id")
    owner = contact.get("user_id")
    phone = (contact.get("phone_number") or "").strip()
    if not phone or sender is None or owner is None or str(owner) != str(sender):
        return None
    return ("+" + phone if not phone.startswith("+") else phone)[:64]


def _save_contact_phone(contact: dict, frm: dict) -> bool:
    """Store a phone number shared from the Mini App's ``requestContact()`` onto
    the sender's linked account. Telegram hands the shared contact to the BOT (not
    the Mini App), so this is where the number actually lands."""
    phone = _clean_contact_phone(contact, frm)
    if not phone:
        return False
    user = SessionLocal.execute(
        select(User).where(User.telegram_id == str(frm.get("id")))
    ).scalar_one_or_none()
    if not user:
        SessionLocal.remove()
        return False
    user.phone = phone
    SessionLocal.commit()
    SessionLocal.remove()
    return True


def _save_share_phone(contact: dict, frm: dict) -> bool:
    """Fill the most recent pending phone-share code for this sender (web sign-up
    'take from Telegram' — the account may not exist yet, so we key by code)."""
    phone = _clean_contact_phone(contact, frm)
    if not phone:
        return False
    row = SessionLocal.execute(
        select(PhoneShare)
        .where(PhoneShare.tg_id == str(frm.get("id")), PhoneShare.phone.is_(None))
        .order_by(PhoneShare.id.desc())
    ).scalars().first()
    if not row:
        SessionLocal.remove()
        return False
    row.phone = phone
    SessionLocal.commit()
    SessionLocal.remove()
    return True


def handle_update(update: dict):
    message = update.get("message")
    if not message:
        return
    chat_id = message.get("chat", {}).get("id")
    frm = message.get("from", {})
    text = (message.get("text") or "").strip()
    if chat_id is None:
        return

    # Phone shared ("take from Telegram"): fill a linked account (Mini App) AND/OR
    # a pending web sign-up share code (desktop). Confirm if either landed.
    contact = message.get("contact")
    if contact:
        ok = _save_contact_phone(contact, frm)
        shared = _save_share_phone(contact, frm)
        msg = TEXTS["phone_share_saved"] if shared else (TEXTS["phone_saved"] if ok else TEXTS["phone_bad"])
        send_message(chat_id, msg, _launch_markup())
        return

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        param = parts[1].strip() if len(parts) > 1 else ""
        if param.startswith("link_"):
            code = param[len("link_"):]
            if _link_account(code, frm):
                send_message(chat_id, TEXTS["linked"], _launch_markup())
            else:
                send_message(chat_id, TEXTS["link_bad"])
            return
        if param.startswith("phone_"):
            # Desktop sign-up asked for the phone via Telegram — remember which code
            # this chat is answering, then prompt them to share their number.
            code = param[len("phone_"):]
            _claim_phone_code(code, frm)
            send_message(chat_id, TEXTS["phone_ask"], _contact_markup())
            return
        send_message(chat_id, TEXTS["welcome"], _launch_markup())
        return

    # Any other message — nudge them to the cabinet.
    send_message(chat_id, TEXTS["already"], _launch_markup())


def run():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not configured")
    init_db()
    set_menu_button()
    print(f"notharduz_bot polling started · mini app: {settings.MINIAPP_URL}")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{API}/getUpdates",
                params={"offset": offset, "timeout": 30, "allowed_updates": json.dumps(["message"])},
                timeout=40,
            )
            data = resp.json()
            if not data.get("ok"):
                time.sleep(3)
                continue
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                try:
                    handle_update(upd)
                except Exception as e:
                    print(f"update error: {e}")
                    SessionLocal.remove()
        except Exception as e:
            print(f"poll error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run()
