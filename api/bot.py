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
from models import User

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


def handle_update(update: dict):
    message = update.get("message")
    if not message:
        return
    chat_id = message.get("chat", {}).get("id")
    frm = message.get("from", {})
    text = (message.get("text") or "").strip()
    if chat_id is None:
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
