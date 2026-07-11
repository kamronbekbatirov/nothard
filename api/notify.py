"""Best-effort Telegram notifications to clients, in their chosen language.

Sends only if the client's account has a linked telegram_id. Non-blocking (fire
in a background thread) so it never slows the API response.
"""

import json
import threading
import urllib.request

from config import settings

LOCALES = ("ru", "en", "uz", "uz-cyrl")

OPEN_LABEL = {
    "ru": "Открыть кабинет",
    "en": "Open cabinet",
    "uz": "Kabinetni ochish",
    "uz-cyrl": "Кабинетни очиш",
}

STATUS_LABEL = {
    "ru": {"new": "Новое", "viewing": "Просмотр назначен", "viewed": "Просмотрено",
           "secured": "Забронировано", "completed": "Оформлено", "busy": "Занято",
           "declined": "Отклонено", "reached": "Связались"},
    "en": {"new": "New", "viewing": "Viewing set", "viewed": "Viewed",
           "secured": "Secured", "completed": "Finalised", "busy": "Taken",
           "declined": "Declined", "reached": "Contacted"},
    "uz": {"new": "Yangi", "viewing": "Ko‘rik belgilandi", "viewed": "Ko‘rildi",
           "secured": "Band qilindi", "completed": "Rasmiylashtirildi", "busy": "Band",
           "declined": "Rad etildi", "reached": "Bog‘lanildi"},
    "uz-cyrl": {"new": "Янги", "viewing": "Кўрик белгиланди", "viewed": "Кўрилди",
                "secured": "Банд қилинди", "completed": "Расмийлаштирилди", "busy": "Банд",
                "declined": "Рад этилди", "reached": "Боғланилди"},
}

TEMPLATES = {
    "manager_assigned": {
        "ru": "👤 Вам назначен менеджер: {name}.",
        "en": "👤 Your manager has been assigned: {name}.",
        "uz": "👤 Sizga menejer tayinlandi: {name}.",
        "uz-cyrl": "👤 Сизга менежер тайинланди: {name}.",
    },
    "runner_assigned": {
        "ru": "🚶 Вам назначен сопровождающий: {name}.",
        "en": "🚶 Your host has been assigned: {name}.",
        "uz": "🚶 Sizga hamroh tayinlandi: {name}.",
        "uz-cyrl": "🚶 Сизга ҳамроҳ тайинланди: {name}.",
    },
    "task_done": {
        "ru": "✅ Ещё один шаг вашего переезда выполнен.",
        "en": "✅ Another step of your relocation is done.",
        "uz": "✅ Ko‘chishingizning yana bir bosqichi bajarildi.",
        "uz-cyrl": "✅ Кўчишингизнинг яна бир босқичи бажарилди.",
    },
    "order_paid": {
        "ru": "💳 Оплата подтверждена.",
        "en": "💳 Payment confirmed.",
        "uz": "💳 To‘lov tasdiqlandi.",
        "uz-cyrl": "💳 Тўлов тасдиқланди.",
    },
    "order_refunded": {
        "ru": "↩️ Оформлен возврат средств.",
        "en": "↩️ A refund has been issued.",
        "uz": "↩️ To‘lov qaytarildi.",
        "uz-cyrl": "↩️ Тўлов қайтарилди.",
    },
    "housing_status": {
        "ru": "🏠 {addr} — статус: {status}.",
        "en": "🏠 {addr} — status: {status}.",
        "uz": "🏠 {addr} — holat: {status}.",
        "uz-cyrl": "🏠 {addr} — ҳолат: {status}.",
    },
    "housing_viewing": {
        "ru": "📅 {addr}: назначен просмотр — {when}.",
        "en": "📅 {addr}: a viewing is set — {when}.",
        "uz": "📅 {addr}: ko‘rik belgilandi — {when}.",
        "uz-cyrl": "📅 {addr}: кўрик белгиланди — {when}.",
    },
    "housing_media": {
        "ru": "📸 {addr}: добавлены фото/видео с просмотра.",
        "en": "📸 {addr}: photos/videos from the viewing were added.",
        "uz": "📸 {addr}: ko‘rikdan foto/video qo‘shildi.",
        "uz-cyrl": "📸 {addr}: кўрикдан фото/видео қўшилди.",
    },
    "file_uploaded": {
        "ru": "📎 В ваш кабинет добавлен новый файл.",
        "en": "📎 A new file was added to your cabinet.",
        "uz": "📎 Kabinetingizga yangi fayl qo‘shildi.",
        "uz-cyrl": "📎 Кабинетингизга янги файл қўшилди.",
    },
}


def loc_of(user) -> str:
    l = getattr(user, "locale", None) or "ru"
    return l if l in LOCALES else "ru"


def status_label(status: str, loc: str) -> str:
    return STATUS_LABEL.get(loc, STATUS_LABEL["ru"]).get(status, status)


def _send_message(token: str, payload: dict) -> bool:
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception:
        return False


def _post(token: str, chat_id: str, text: str, reply_markup: dict | None = None):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if _send_message(token, payload):
        return
    # Fallback: if the inline Mini App button was rejected for any reason, still
    # deliver the plain text so the client never misses a notification.
    if reply_markup:
        _send_message(token, {"chat_id": chat_id, "text": text, "disable_web_page_preview": True})


def send(user, event: str, **params):
    """Send a localized notification to the user's Telegram (if linked)."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not user or not getattr(user, "telegram_id", None) or not token:
        return
    loc = loc_of(user)
    tmpl = TEMPLATES.get(event, {}).get(loc) or TEMPLATES.get(event, {}).get("ru")
    if not tmpl:
        return
    if "status_key" in params:
        params["status"] = status_label(params.pop("status_key"), loc)
    try:
        text = tmpl.format(**params)
    except Exception:
        text = tmpl
    # An inline "Open cabinet" button that launches the Mini App directly (opens
    # the landing, which silently resumes the already-registered user into their
    # cabinet) — no link to tap through. web_app buttons work in private chats.
    url = f"{settings.FRONTEND_BASE_URL}/{loc}"
    markup = {"inline_keyboard": [[{"text": OPEN_LABEL[loc], "web_app": {"url": url}}]]}
    threading.Thread(
        target=_post, args=(token, str(user.telegram_id), text, markup), daemon=True
    ).start()
