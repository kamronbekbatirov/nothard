import json
import os
import re
import secrets
import threading
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, redirect, g, send_from_directory
from flask_cors import CORS
from sqlalchemy import select, func
from werkzeug.utils import secure_filename

from config import settings
from db import SessionLocal, init_db
from models import (
    User, Client, Order, Task, Listing, Message, Review,
    HousingItem, HousingMedia, Attachment, Session,
)
from catalog import (
    SERVICE_PRICE,
    VIEWING_PRICE,
    PACKAGE_AMOUNT,
    PACKAGE_STEPS,
    RUNNER_STEPS,
    RUNNER_SERVICES,
    RUNNER_VISIT_FEE,
    docs_for_package,
    docs_for_service,
)
from security import (
    hash_password,
    verify_password,
    make_access_token,
    make_refresh_token,
    decode_token,
    parse_user_agent,
)
from telegram_initdata import validate_init_data
import telegram_oidc as oidc
import mailer
import notify


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": settings.CORS_ORIGINS}}, supports_credentials=False)
    init_db()

    # ---- session lifecycle -------------------------------------------------
    @app.teardown_appcontext
    def _remove_session(exc=None):
        SessionLocal.remove()

    # ---- helpers -----------------------------------------------------------
    def _client_ip() -> str:
        """Real client IP behind the Caddy reverse proxy."""
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()[:64]
        return (request.remote_addr or "")[:64]

    def start_session(user_id: int) -> int:
        """Create (or reuse) the Session row for the requesting device and return
        its id. Dedups on the client-provided device_id so a logout→login on the
        same device maps back to one session instead of accumulating duplicates."""
        device_id = (request.headers.get("X-Device-Id") or "").strip()[:64] or None
        ua = (request.headers.get("User-Agent") or "")[:512]
        info = parse_user_agent(ua)
        sess = None
        if device_id:
            sess = SessionLocal.execute(
                select(Session).where(
                    Session.user_id == user_id, Session.device_id == device_id
                )
            ).scalars().first()
        if sess is None:
            sess = Session(user_id=user_id, device_id=device_id)
            SessionLocal.add(sess)
        sess.ip = _client_ip()
        sess.user_agent = ua
        sess.browser = info["browser"]
        sess.os = info["os"]
        sess.device = info["device"]
        sess.revoked = False
        sess.last_seen_at = datetime.utcnow()
        SessionLocal.commit()
        return sess.id

    def current_sid() -> int | None:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        payload = decode_token(auth[7:])
        return payload.get("sid") if payload else None

    def current_user() -> User | None:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        payload = decode_token(auth[7:])
        if not payload or payload.get("type") != "access":
            return None
        try:
            uid = int(payload["sub"])
        except (KeyError, ValueError):
            return None
        sid = payload.get("sid")
        if sid is not None:
            # Token is bound to a session — honor revocation (logout / "sign out
            # other sessions" / account deletion all revoke or remove the row).
            sess = SessionLocal.get(Session, int(sid))
            if not sess or sess.revoked or sess.user_id != uid:
                return None
            try:
                if (datetime.utcnow() - sess.last_seen_at).total_seconds() > 120:
                    sess.last_seen_at = datetime.utcnow()
                    ip = _client_ip()
                    if ip:
                        sess.ip = ip
                    SessionLocal.commit()
            except Exception:
                SessionLocal.rollback()
        user = SessionLocal.get(User, uid)
        # A deactivated (banned) or deleted account can't use existing tokens.
        if user is None or not user.is_active:
            return None
        return user

    def require_user():
        u = current_user()
        if not u:
            return None, (jsonify({"error": "unauthorized"}), 401)
        return u, None

    def require_role(*roles):
        u = current_user()
        if not u:
            return None, (jsonify({"error": "unauthorized"}), 401)
        allowed = set(roles)
        if "operator" in allowed:
            allowed.add("admin")  # admin is a superset of operator
        if u.role not in allowed:
            return None, (jsonify({"error": "forbidden"}), 403)
        return u, None

    def runner_name_map() -> dict:
        return {
            u.id: u.name
            for u in SessionLocal.execute(select(User).where(User.role == "runner")).scalars().all()
        }

    def manager_users():
        return SessionLocal.execute(
            select(User).where(User.role.in_(["operator", "admin"])).order_by(User.id)
        ).scalars().all()

    def manager_name_map() -> dict:
        return {u.id: u.name for u in manager_users()}

    # ---- domain helpers ----------------------------------------------------
    def get_or_create_client(user: User) -> Client:
        c = SessionLocal.execute(
            select(Client).where(Client.user_id == user.id)
        ).scalar_one_or_none()
        if c is None:
            c = Client(user_id=user.id, name=user.name or "Client")
            SessionLocal.add(c)
            SessionLocal.flush()
        return c

    def client_tasks(client_id: int):
        return SessionLocal.execute(
            select(Task).where(Task.client_id == client_id).order_by(Task.position, Task.id)
        ).scalars().all()

    def client_orders(client_id: int):
        return SessionLocal.execute(
            select(Order).where(Order.client_id == client_id).order_by(Order.id)
        ).scalars().all()

    def in_progress_service_ids(client_id: int) -> set:
        """Service ids that currently have an unfinished order — the ONLY reason to
        block a re-purchase. A completed (done) service can be bought again as new,
        so a finished 'sim card' etc. re-appears as a fresh active order."""
        tasks = client_tasks(client_id)
        svc_task_by_order = {t.order_id: t for t in tasks if t.kind == "service" and t.order_id}
        ids = set()
        for o in client_orders(client_id):
            if o.item_type == "service" and not o.archived:
                st = svc_task_by_order.get(o.id)
                if not (st and st.status == "done"):
                    ids.add(o.item_id)
        return ids

    HOUSING_KEYS = {"housingSearch", "viewings"}
    # new → viewing → viewed → secured → completed (or busy / declined)
    HOUSING_STATUSES = {"new", "viewing", "viewed", "reached", "busy", "secured", "completed", "declined"}
    # Package step tasks that produce a document the operator can upload.
    FILE_STEPS = {"lease", "bank", "nhs"}

    def notify_client(client, event, **params):
        """Send a Telegram notification to the client (if linked), in their language."""
        if client and client.user_id:
            u = SessionLocal.get(User, client.user_id)
            if u:
                notify.send(u, event, **params)

    def notify_task_done(client, task):
        """A task just completed. If it finishes a reviewable order (a service, or
        the last step of a package), invite the client to leave a review; otherwise
        just report the intermediate step. Keeps the '🎉 all done → review' Telegram
        message in sync with the cabinet's review prompt."""
        if task.kind == "service":
            notify_client(client, "review_request")
            return
        # Package step — is the whole package now complete?
        if task.order_id:
            steps = [
                t for t in client_tasks(client.id)
                if t.kind == "step" and t.order_id == task.order_id
            ]
            if steps and all(t.status == "done" for t in steps):
                notify_client(client, "review_request")
                return
        notify_client(client, "task_done")

    def _document_files(step_tasks) -> dict:
        docs = [t for t in step_tasks if t.key in FILE_STEPS]
        att = task_attachments([t.id for t in docs])
        return {t.key: att.get(t.id, []) for t in docs if att.get(t.id)}

    def order_attachments(order_ids):
        ids = list(order_ids)
        if not ids:
            return {}
        rows = SessionLocal.execute(
            select(Attachment).where(Attachment.order_id.in_(ids)).order_by(Attachment.id)
        ).scalars().all()
        out: dict = {}
        for a in rows:
            out.setdefault(a.order_id, []).append(
                {"id": a.id, "filename": a.filename, "url": a.url}
            )
        return out

    def task_attachments(task_ids):
        ids = list(task_ids)
        if not ids:
            return {}
        rows = SessionLocal.execute(
            select(Attachment).where(Attachment.task_id.in_(ids)).order_by(Attachment.id)
        ).scalars().all()
        out: dict = {}
        for a in rows:
            out.setdefault(a.task_id, []).append(
                {"id": a.id, "filename": a.filename, "url": a.url}
            )
        return out

    def client_housing(client_id: int):
        return SessionLocal.execute(
            select(HousingItem).where(HousingItem.client_id == client_id).order_by(HousingItem.id)
        ).scalars().all()

    def housing_media(housing_ids):
        ids = list(housing_ids)
        if not ids:
            return {}
        rows = SessionLocal.execute(
            select(HousingMedia).where(HousingMedia.housing_id.in_(ids)).order_by(HousingMedia.id)
        ).scalars().all()
        out: dict = {}
        for m in rows:
            out.setdefault(m.housing_id, []).append(
                {"id": m.id, "url": m.url, "filename": m.filename, "kind": m.kind}
            )
        return out

    def housing_rows(items) -> list:
        media = housing_media([h.id for h in items])
        # Properties the client has paid £30 to have accompanied-viewed. Derived
        # from viewing Orders (item_id == housing id) so no extra column is needed.
        viewing_ids: set[int] = set()
        cids = {h.client_id for h in items}
        if cids:
            for o in SessionLocal.execute(
                select(Order).where(Order.client_id.in_(cids), Order.item_type == "viewing")
            ).scalars().all():
                try:
                    viewing_ids.add(int(o.item_id))
                except (TypeError, ValueError):
                    pass
        return [
            {
                "id": h.id, "source": h.source, "ref": h.ref, "title": h.title,
                "description": h.description, "priceGBP": h.price_gbp, "addr": h.addr,
                "photoUrl": h.photo_url, "status": h.status, "viewingAt": h.viewing_at,
                "note": h.note, "media": media.get(h.id, []),
                "viewingRequested": h.id in viewing_ids,
            }
            for h in items
        ]

    def housing_row(h: HousingItem) -> dict:
        return housing_rows([h])[0]

    def _og_tag(html: str, *props) -> str | None:
        for prop in props:
            m = re.search(
                rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']*)["\']',
                html, re.I,
            ) or re.search(
                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{prop}["\']',
                html, re.I,
            )
            if m and m.group(1).strip():
                return m.group(1).strip()
        return None

    def _clean(s: str) -> str:
        # Un-escape the few HTML entities that show up in OG meta content.
        for a, b in (("&amp;", "&"), ("&#163;", "£"), ("&pound;", "£"),
                     ("&#39;", "'"), ("&quot;", '"'), ("&nbsp;", " ")):
            s = s.replace(a, b)
        return s.strip()

    def fetch_og_meta(url: str) -> dict:
        """Best-effort scrape of a listing's OpenGraph tags (image/title/desc/price).
        Mimics the Telegram link-preview bot — many sites (incl. Rightmove) serve OG
        tags to it that they hide from generic scrapers. Returns {} on failure."""
        if not url.lower().startswith(("http://", "https://")):
            return {}
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "TelegramBot (like TwitterBot)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read(500000).decode("utf-8", "ignore")
        except Exception:
            return {}

        out: dict = {}
        img = _og_tag(html, "og:image", "twitter:image", "twitter:image:src")
        if img:
            if img.startswith("//"):
                img = "https:" + img
            if img.startswith("http"):
                out["photo"] = _clean(img)[:512]

        desc = _og_tag(html, "og:description", "twitter:description", "description")
        title = _og_tag(html, "og:title", "twitter:title")
        if desc:
            out["description"] = _clean(desc)[:512]
        # Prefer the description as the human title (it carries type + address),
        # since many sites' og:title is generic ("Check out this flat on …").
        nice = None
        if desc:
            nice = re.split(r"\s+for\s+£", _clean(desc))[0]
        if not nice and title and not re.match(r"(check out|property to rent)", title, re.I):
            nice = _clean(title)
        if nice:
            out["title"] = nice[:255]

        # Pull a monthly price (£1,800 pcm / per month) from title or description.
        for text in (desc or "", title or ""):
            m = re.search(r"£\s?([\d,]+)\s*(?:pcm|per month|/mo|a month)", text, re.I) or \
                re.search(r"£\s?([\d,]+)", text)
            if m:
                try:
                    out["price"] = int(m.group(1).replace(",", ""))
                    break
                except ValueError:
                    pass
        return out

    def has_housing_search(tasks) -> bool:
        return any(
            (t.kind == "step" and t.key in HOUSING_KEYS)
            or (t.kind == "service" and t.key == "housingSearch")
            for t in tasks
        )

    def _purge_client(client_id: int):
        """Delete every row that references a client, before removing the client."""
        for model in (HousingMedia, Attachment, HousingItem, Review, Message, Task, Order):
            SessionLocal.execute(model.__table__.delete().where(model.client_id == client_id))

    def _delete_user_sessions(user_id: int):
        """Remove a user's sessions (FK to users) before the user is deleted."""
        SessionLocal.execute(Session.__table__.delete().where(Session.user_id == user_id))

    def _revoke_user_sessions(user_id: int):
        """Invalidate all of a user's active sessions (e.g. on deactivation)."""
        SessionLocal.execute(
            Session.__table__.update()
            .where(Session.user_id == user_id)
            .values(revoked=True)
        )

    def make_package_tasks(client: Client, order: Order, pkg: str):
        base = max((t.position for t in client_tasks(client.id)), default=-1) + 1
        for i, key in enumerate(PACKAGE_STEPS.get(pkg, [])):
            SessionLocal.add(
                Task(
                    client_id=client.id,
                    order_id=order.id,
                    kind="step",
                    key=key,
                    status="todo",
                    runner_id=client.runner_id if key in RUNNER_STEPS else None,
                    position=base + i,
                )
            )

    def make_service_task(client: Client, order: Order, service_id: str):
        base = max((t.position for t in client_tasks(client.id)), default=-1) + 1
        SessionLocal.add(
            Task(
                client_id=client.id,
                order_id=order.id,
                kind="service",
                key=service_id,
                status="todo",
                runner_id=client.runner_id if service_id in RUNNER_SERVICES else None,
                position=base,
            )
        )

    def recompute_docs(client: Client):
        """Rebuild the documents checklist from what the client currently owns."""
        relevant: set[str] = set()
        for o in client_orders(client.id):
            relevant |= set(
                docs_for_package(o.item_id) if o.item_type == "package" else docs_for_service(o.item_id)
            )
        client.documents = {k: (client.documents or {}).get(k, False) for k in relevant}

    def delete_order(order: Order):
        """Remove an order and everything derived from it (tasks + their files, reviews)."""
        task_ids = [
            t.id for t in SessionLocal.execute(
                select(Task).where(Task.order_id == order.id)
            ).scalars().all()
        ]
        if task_ids:
            SessionLocal.execute(Attachment.__table__.delete().where(Attachment.task_id.in_(task_ids)))
        SessionLocal.execute(Attachment.__table__.delete().where(Attachment.order_id == order.id))
        SessionLocal.execute(Review.__table__.delete().where(Review.order_id == order.id))
        SessionLocal.execute(Task.__table__.delete().where(Task.order_id == order.id))
        SessionLocal.delete(order)

    def active_step_index(step_tasks) -> int:
        """First non-done step is the 'current' step (0-based)."""
        for i, t in enumerate(step_tasks):
            if t.status != "done":
                return i
        return max(len(step_tasks) - 1, 0)

    def task_public(t: Task) -> dict:
        return {"kind": t.kind, "key": t.key, "status": t.status, "time": t.time, "addr": t.addr}

    def issue(user: User):
        sid = start_session(user.id)
        return {
            "access_token": make_access_token(user.id, sid),
            "refresh_token": make_refresh_token(user.id),
            "user": user.to_public(),
        }

    def gen_code() -> str:
        return f"{secrets.randbelow(1000000):06d}"

    def _download_bytes(url: str) -> bytes | None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NothardBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.read(6_000_000)
        except Exception:
            return None

    def _telegram_photo_url(tg_id: str) -> str | None:
        """Resolve a Telegram user's profile-photo download URL via the Bot API.
        Best-effort — returns None if the user's privacy hides the photo from bots."""
        token = settings.TELEGRAM_BOT_TOKEN
        if not token or not tg_id:
            return None
        try:
            u = f"https://api.telegram.org/bot{token}/getUserProfilePhotos?user_id={tg_id}&limit=1"
            with urllib.request.urlopen(u, timeout=8) as r:
                res = json.loads(r.read())
            photos = (res.get("result") or {}).get("photos") or []
            if not photos or not photos[0]:
                return None
            file_id = photos[0][-1]["file_id"]  # largest size
            gf = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
            with urllib.request.urlopen(gf, timeout=8) as r:
                fres = json.loads(r.read())
            path = (fres.get("result") or {}).get("file_path")
            return f"https://api.telegram.org/file/bot{token}/{path}" if path else None
        except Exception:
            return None

    def ensure_tg_photo(user: User, fallback_url: str | None = None):
        """Refresh the user's avatar from Telegram (background thread, never delays
        login). Writes to a STABLE per-user file (``tg_<id>.jpg``) with an atomic
        overwrite, so the file that the browser is currently displaying is never
        deleted out from under it — this fixes the Mini App "?" flicker where a
        re-login on every open was deleting the previous avatar mid-render. A
        ``?v=`` cache-buster on the URL makes a changed photo refresh anyway.

        Source priority:
        1. The URL Telegram hands us at login (OIDC ``picture`` / Mini App
           ``photo_url``) — respects "profile photo → Everybody".
        2. The Bot API ``getUserProfilePhotos`` (stricter privacy gate) as fallback.
        """
        uid = user.id
        tg_id = user.telegram_id

        def work():
            data = _download_bytes(fallback_url) if fallback_url else None
            if not data and tg_id:
                turl = _telegram_photo_url(tg_id)
                if turl:
                    data = _download_bytes(turl)
            if not data:
                return
            fname = f"tg_{uid}.jpg"
            dest = os.path.join(UPLOAD_DIR, fname)
            tmp = os.path.join(UPLOAD_DIR, f".tmp_{uuid.uuid4().hex}.jpg")
            try:
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dest)  # atomic — the served file is never missing
            except OSError:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                return
            s = SessionLocal()
            try:
                u = s.get(User, uid)
                if u:
                    u.photo_url = f"/api/uploads/{fname}?v={int(datetime.utcnow().timestamp())}"
                    s.commit()
            finally:
                SessionLocal.remove()

        threading.Thread(target=work, daemon=True).start()

    def front(path: str):
        return redirect(f"{settings.FRONTEND_BASE_URL}{path}", code=302)

    def bot_deeplink(param: str) -> str:
        return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={param}"

    # ---- health ------------------------------------------------------------
    @app.get("/")
    def health():
        return jsonify({"ok": True, "service": "nothard-api"})

    # ---- email auth --------------------------------------------------------
    @app.post("/auth/register")
    def register():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip() or None
        if not email or not password or not name:
            return jsonify({"error": "missing_fields"}), 400
        exists = SessionLocal.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if exists:
            return jsonify({"error": "email already registered", "code": "email_taken"}), 409
        loc = (data.get("locale") or "ru").strip()
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            phone=phone,
            role="client",
            locale=loc if loc in ("ru", "en", "uz", "uz-cyrl") else "ru",
        )
        SessionLocal.add(user)
        SessionLocal.commit()
        return jsonify(issue(user)), 201

    @app.post("/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        user = SessionLocal.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if (
            not user
            or not user.password_hash
            or not verify_password(password, user.password_hash)
            or not user.is_active
        ):
            return jsonify({"error": "invalid credentials"}), 401
        return jsonify(issue(user))

    # ---- Passwordless email login (send a code, then verify) --------------
    @app.post("/auth/email/request")
    def auth_email_request():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        user = SessionLocal.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user and user.is_active:
            user.email_code = gen_code()
            user.email_code_expires = datetime.utcnow() + timedelta(minutes=15)
            SessionLocal.commit()
            mailer.send_code(email, user.email_code)
        # Always OK — don't reveal whether the email exists.
        return jsonify({"ok": True})

    @app.post("/auth/email/verify")
    def auth_email_verify():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        code = (data.get("code") or "").strip()
        user = SessionLocal.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user or not user.email_code or not user.is_active:
            return jsonify({"error": "wrong code", "code": "bad_code"}), 400
        if user.email_code_expires and datetime.utcnow() > user.email_code_expires:
            return jsonify({"error": "code expired", "code": "expired"}), 400
        if code != user.email_code:
            return jsonify({"error": "wrong code", "code": "bad_code"}), 400
        user.email_code = None
        user.email_code_expires = None
        SessionLocal.commit()
        return jsonify(issue(user))

    @app.get("/auth/me")
    def me():
        user, err = require_user()
        if err:
            return err
        return jsonify(user.to_public())

    # ---- Telegram Mini App login (initData) --------------------------------
    @app.post("/auth/telegram/miniapp")
    def tg_miniapp():
        data = request.get_json(silent=True) or {}
        init_data = data.get("init_data") or ""
        parsed = validate_init_data(init_data)
        if not parsed or not parsed.get("user"):
            return jsonify({"error": "invalid init data"}), 401
        tg = parsed["user"]
        tg_id = str(tg.get("id"))
        photo = tg.get("photo_url")
        user = SessionLocal.execute(
            select(User).where(User.telegram_id == tg_id)
        ).scalar_one_or_none()
        if user is None:
            # `existing_only` = the landing's silent "resume" probe: log in a
            # returning user, but DON'T create an account for a first-time visitor
            # (they should see the landing and choose to sign up explicitly).
            if data.get("existing_only"):
                return jsonify({"exists": False})
            name = " ".join(x for x in [tg.get("first_name"), tg.get("last_name")] if x) or (
                tg.get("username") or "Telegram User"
            )
            user = User(
                name=name[:255],
                role="client",
                telegram_id=tg_id,
                telegram_username=tg.get("username"),
            )
            SessionLocal.add(user)
            SessionLocal.commit()
        elif not user.is_active:
            return jsonify({"error": "account disabled", "code": "disabled"}), 403
        # Always keep a local avatar (initData photo_url expires / is cross-origin).
        ensure_tg_photo(user, fallback_url=photo)
        return jsonify(issue(user))

    # ---- Telegram OIDC login / link ---------------------------------------
    @app.get("/auth/telegram/start")
    def tg_start():
        if not oidc.is_configured():
            return front(f"/{settings.DEFAULT_LOCALE}/login?tg_error=unconfigured")
        return redirect(oidc.create_authorization_url("login", None), code=302)

    @app.get("/auth/telegram/link-start")
    def tg_link_start():
        user, err = require_user()
        if err:
            return err
        if oidc.is_configured():
            return jsonify({"url": oidc.create_authorization_url("link", user.id)})
        # Fallback: link through the bot deep-link (works with just the bot token).
        code = secrets.token_urlsafe(12)
        user.tg_link_code = code
        SessionLocal.commit()
        return jsonify({"url": bot_deeplink(f"link_{code}")})

    @app.get("/auth/telegram/callback")
    def tg_callback():
        error = request.args.get("error", "")
        state = request.args.get("state", "")
        code = request.args.get("code", "")
        loc = settings.DEFAULT_LOCALE
        if error:
            return front(f"/{loc}/login?tg_error={error}")
        st = oidc.pop_state(state)
        if not st:
            return front(f"/{loc}/login?tg_error=expired")
        try:
            id_token = oidc.exchange_code(code, st["verifier"])
            claims = oidc.validate_id_token(id_token)
        except Exception:
            return front(f"/{loc}/login?tg_error=verify")

        # IMPORTANT: use the real Telegram user id (`id`), NOT `sub` (an opaque
        # per-app subject). The Mini App initData uses `id`, so aligning on it
        # keeps web-login and bot-login as the same account.
        tg_id = str(claims.get("id") or claims.get("sub") or "")
        if not tg_id:
            return front(f"/{loc}/login?tg_error=noid")
        tg_username = claims.get("preferred_username")
        tg_name = (claims.get("name") or tg_username or "Telegram User")[:255]
        tg_photo = claims.get("picture")

        if st["mode"] == "link":
            user = SessionLocal.get(User, st["user_id"])
            if user is None:
                return front(f"/{loc}/login?tg_error=session")
            taken = SessionLocal.execute(
                select(User).where(User.telegram_id == tg_id)
            ).scalar_one_or_none()
            if taken and taken.id != user.id:
                return front(f"/{loc}/profile?tg=taken")
            user.telegram_id = tg_id
            user.telegram_username = tg_username
            SessionLocal.commit()
            ensure_tg_photo(user, fallback_url=tg_photo)
            return front(f"/{loc}/profile?tg=linked")

        user = SessionLocal.execute(
            select(User).where(User.telegram_id == tg_id)
        ).scalar_one_or_none()
        if user is None:
            user = User(name=tg_name, role="client", telegram_id=tg_id,
                        telegram_username=tg_username)
            SessionLocal.add(user)
            SessionLocal.commit()
        elif not user.is_active:
            return front(f"/{loc}/login?tg_error=disabled")
        ensure_tg_photo(user, fallback_url=tg_photo)

        ticket = oidc.store_ticket(make_access_token(user.id), make_refresh_token(user.id), user.role)
        return front(f"/{loc}/auth/telegram/callback?ticket={ticket}")

    @app.post("/auth/telegram/exchange")
    def tg_exchange():
        data = request.get_json(silent=True) or {}
        payload = oidc.pop_ticket(data.get("ticket") or "")
        if not payload:
            return jsonify({"error": "invalid or expired ticket"}), 400
        p = decode_token(payload["access"])
        user = SessionLocal.get(User, int(p["sub"])) if p else None
        if not user:
            return jsonify({"error": "invalid or expired ticket"}), 400
        # Re-issue here: this POST is the real device's fetch, so it carries the
        # device_id / UA / IP we want on the session (the OIDC redirect did not).
        return jsonify(issue(user))

    @app.post("/auth/telegram/unlink")
    def tg_unlink():
        user, err = require_user()
        if err:
            return err
        # Need another way in (email or password) so the account stays reachable.
        if not user.password_hash and not user.email:
            return jsonify(
                {"error": "link an email or set a password first", "code": "need_login_method"}
            ), 400
        user.telegram_id = None
        user.telegram_username = None
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.post("/auth/logout")
    def logout_session():
        """Revoke the current device's session so its token stops working."""
        sid = current_sid()
        if sid is not None:
            sess = SessionLocal.get(Session, int(sid))
            if sess:
                sess.revoked = True
                SessionLocal.commit()
        return jsonify({"ok": True})

    # ---- cabinet dashboard -------------------------------------------------
    def manager_block(c: Client | None) -> dict:
        if c and c.manager_id:
            u = SessionLocal.get(User, c.manager_id)
            if u:
                return {"assigned": True, "name": u.name, "hours": "9:00–17:00",
                        "photoUrl": u.photo_url, "telegram": u.telegram_username, "phone": u.phone}
        return {"assigned": False, "name": None, "hours": "9:00–17:00",
                "photoUrl": None, "telegram": None, "phone": None}

    def runner_block(c: Client | None) -> dict:
        if c and c.runner_id:
            u = SessionLocal.get(User, c.runner_id)
            if u:
                return {"assigned": True, "name": u.name, "photoUrl": u.photo_url,
                        "telegram": u.telegram_username, "phone": u.phone}
        return {"assigned": False, "name": None, "photoUrl": None, "telegram": None, "phone": None}

    def dashboard_payload(user: User) -> dict:
        c = SessionLocal.execute(
            select(Client).where(Client.user_id == user.id)
        ).scalar_one_or_none()
        base = {
            "user": user.to_public(),
            "telegram": {"linked": bool(user.telegram_id), "username": user.telegram_username},
            "hasPassword": bool(user.password_hash),
            "manager": manager_block(c),
        }
        if c is None:
            return {**base, "state": "empty", "hasOrders": False, "package": None,
                    "packageComplete": False, "pendingReview": None, "services": [],
                    "documents": {}, "path": [], "runner": runner_block(None),
                    "needsRunner": False, "history": [], "runnerChatAvailable": False}

        orders = client_orders(c.id)
        tasks = client_tasks(c.id)
        # Key service tasks by ORDER, not by service id: buying the same service
        # again (after completing it) yields a new order+task with the same key,
        # so a key-based lookup would resolve the new order to the old done task.
        svc_task_by_order = {t.order_id: t for t in tasks if t.kind == "service" and t.order_id}
        attach_map = order_attachments([o.id for o in orders if o.item_type == "service"])

        def svc_done(o: Order) -> bool:
            st = svc_task_by_order.get(o.id)
            return bool(st and st.status == "done")

        def svc_status(o: Order) -> str:
            st = svc_task_by_order.get(o.id)
            return st.status if st else "todo"

        # Active package = the most recent package the client hasn't archived yet.
        pkg_order = next(
            (o for o in reversed(orders) if o.item_type == "package" and not o.archived), None
        )
        # Services split: active/awaiting-ack (not archived) vs acknowledged-done (archived).
        svc_active = [o for o in orders if o.item_type == "service" and not o.archived]
        svc_archived = [o for o in orders if o.item_type == "service" and o.archived]

        pkg_steps = [
            t for t in tasks if t.kind == "step" and pkg_order and t.order_id == pkg_order.id
        ]
        package_complete = bool(pkg_order) and bool(pkg_steps) and all(
            t.status == "done" for t in pkg_steps
        )

        # A runner (field companion) is only relevant while there's ACTIVE in-person
        # work left: a not-yet-done runner step (airport meet / viewings / move-in) or
        # a not-yet-done runner service (transport / moving). Once every field visit is
        # done the companion card disappears (the manager stays). Plain admin services
        # (e.g. Oyster) never need one.
        needs_runner = any(
            t.key in RUNNER_STEPS and t.status != "done" for t in pkg_steps
        ) or any(
            o.item_id in RUNNER_SERVICES and not svc_done(o) for o in svc_active
        )

        # Review prompt queue: a completed-but-unacknowledged package, then any
        # completed-but-unacknowledged service. (archived == acknowledged.)
        pending_review = None
        if pkg_order and package_complete:
            pending_review = {
                "orderId": pkg_order.id, "itemType": "package",
                "itemId": pkg_order.item_id, "amountGBP": pkg_order.amount_gbp,
            }
        else:
            for o in svc_active:
                if svc_done(o):
                    pending_review = {
                        "orderId": o.id, "itemType": "service",
                        "itemId": o.item_id, "amountGBP": o.amount_gbp,
                    }
                    break

        def svc_row(o: Order) -> dict:
            return {
                "id": o.item_id, "amountGBP": o.amount_gbp, "paid": o.paid,
                "taskStatus": svc_status(o), "done": svc_done(o),
                "attachments": attach_map.get(o.id, []),
            }

        services = [svc_row(o) for o in svc_active]
        completed_services = [svc_row(o) for o in svc_archived]

        # Full order history — what the client bought, its status, and when each part
        # was completed. Kept even after a package is archived, so a finished client
        # keeps a record of previous relocations/services in their cabinet.
        steps_by_order: dict = {}
        for t in tasks:
            if t.kind == "step" and t.order_id:
                steps_by_order.setdefault(t.order_id, []).append(t)

        def _iso_z(dt):
            return dt.isoformat() + "Z" if dt else None

        history = []
        for o in orders:
            row = {
                "type": o.item_type, "id": o.item_id, "amountGBP": o.amount_gbp,
                "paid": o.paid, "createdAt": _iso_z(o.created_at),
            }
            if o.item_type == "package":
                osteps = sorted(steps_by_order.get(o.id, []), key=lambda x: (x.position, x.id))
                comp = [s.completed_at for s in osteps if s.completed_at]
                done = bool(osteps) and all(s.status == "done" for s in osteps)
                row["status"] = "done" if done else "active"
                row["completedAt"] = _iso_z(max(comp)) if (done and comp) else None
                row["steps"] = [
                    {"key": s.key, "status": s.status, "completedAt": _iso_z(s.completed_at)}
                    for s in osteps
                ]
            else:
                st = svc_task_by_order.get(o.id)
                done = bool(st and st.status == "done")
                row["status"] = "done" if done else "active"
                row["completedAt"] = _iso_z(st.completed_at) if (st and done) else None
            history.append(row)
        history.reverse()  # newest first

        if not orders:
            state = "empty"
        elif pkg_order is not None or svc_active:
            state = "active"
        else:
            state = "completed"

        return {
            **base,
            "state": state,
            "hasOrders": bool(orders),
            "documents": c.documents or {},
            "runner": runner_block(c),
            "needsRunner": needs_runner,
            "package": (
                {"id": pkg_order.item_id, "amountGBP": pkg_order.amount_gbp,
                 "paid": pkg_order.paid, "status": pkg_order.status,
                 "complete": package_complete, "orderId": pkg_order.id,
                 "details": pkg_order.details or {},
                 "hasAirportMeet": pkg_order.item_id in {"meet", "premium"}}
                if pkg_order else None
            ),
            "packageComplete": package_complete,
            "pendingReview": pending_review,
            "services": services,
            "completedServices": completed_services,
            "path": [task_public(t) for t in pkg_steps],
            "documentFiles": _document_files(pkg_steps),
            "housingSearch": has_housing_search(tasks),
            "housing": housing_rows(client_housing(c.id)),
            "history": history,
            # The client may chat with their companion only once a runner is assigned.
            "runnerChatAvailable": bool(c.runner_id),
        }

    @app.get("/me/dashboard")
    @app.get("/me/profile")
    def my_dashboard():
        user, err = require_user()
        if err:
            return err
        return jsonify(dashboard_payload(user))

    # ---- Public "share your relocation with family" link -------------------
    def _first_name(name: str) -> str:
        return (name or "").strip().split(" ")[0] if name else ""

    @app.post("/me/share")
    def my_share_link():
        """Create (or return) a stable public token for a read-only relocation page
        the client can send to family. Idempotent."""
        user, err = require_user()
        if err:
            return err
        c = get_or_create_client(user)
        if not c.share_token:
            c.share_token = secrets.token_urlsafe(12)[:24]
            SessionLocal.commit()
        return jsonify({"token": c.share_token})

    @app.get("/share/<token>")
    def public_share(token: str):
        """Public, unauthenticated read-only snapshot of a client's relocation:
        package, progress, path statuses, and manager/companion names + photos.
        Deliberately excludes all contacts, chat, documents and addresses."""
        c = SessionLocal.execute(
            select(Client).where(Client.share_token == token)
        ).scalar_one_or_none()
        if not c or not token:
            return jsonify({"error": "not found"}), 404
        orders = client_orders(c.id)
        tasks = client_tasks(c.id)
        pkg_order = next(
            (o for o in reversed(orders) if o.item_type == "package" and not o.archived), None
        )
        pkg_steps = [
            t for t in tasks if t.kind == "step" and pkg_order and t.order_id == pkg_order.id
        ]
        done = sum(1 for t in pkg_steps if t.status == "done")
        total = len(pkg_steps)

        def person(uid):
            if not uid:
                return None
            u = SessionLocal.get(User, uid)
            return {"name": u.name, "photoUrl": u.photo_url} if u else None

        svc_task_by_order = {t.order_id: t for t in tasks if t.kind == "service" and t.order_id}
        services = [
            {"id": o.item_id,
             "done": bool(svc_task_by_order.get(o.id) and svc_task_by_order[o.id].status == "done")}
            for o in orders if o.item_type == "service" and not o.archived
        ]
        return jsonify({
            "clientName": _first_name(c.name),
            "package": ({"id": pkg_order.item_id} if pkg_order else None),
            "packageComplete": bool(pkg_steps) and done == total and total > 0,
            "progress": {"done": done, "total": total},
            "path": [{"key": t.key, "status": t.status} for t in pkg_steps],
            "services": services,
            "manager": person(c.manager_id),
            "runner": person(c.runner_id),
        })

    @app.post("/me/checkout")
    def my_checkout():
        """Create (and mark paid) orders for a package and/or services, then
        generate the corresponding tasks. Simulates a successful Payme payment."""
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        items = data.get("items") or []
        details = data.get("details") or {}
        if isinstance(details, dict):
            # Auto-fill the account name if the user provided one and had none.
            nm = (details.get("name") or "").strip()
            if nm and not (user.name or "").strip():
                user.name = nm[:255]
        client = get_or_create_client(user)
        # Only an in-progress order blocks re-buying; a completed service can be
        # purchased again as a fresh order.
        existing_services = in_progress_service_ids(client.id)
        for item in items:
            itype = item.get("type")
            iid = item.get("id")
            if itype == "package" and iid in PACKAGE_AMOUNT:
                # A new package replaces the current ACTIVE one (cumulative upgrade),
                # but keeps archived/completed packages as history (they may have reviews).
                new_details = dict(details) if isinstance(details, dict) else {}
                for o in client_orders(client.id):
                    if o.item_type == "package" and not o.archived:
                        # Carry over arrival details on upgrade if the new order omits them.
                        for k in ("arrivalDate", "arrivalTime", "airport", "flight"):
                            if not new_details.get(k) and (o.details or {}).get(k):
                                new_details[k] = o.details[k]
                        delete_order(o)
                SessionLocal.flush()
                order = Order(client_id=client.id, item_type="package", item_id=iid,
                              amount_gbp=PACKAGE_AMOUNT[iid], paid=True, status="active",
                              details=new_details)
                SessionLocal.add(order)
                SessionLocal.flush()
                make_package_tasks(client, order, iid)
                if new_details.get("arrivalDate"):
                    mark_airport_meet_active(client, order)
            elif itype == "service" and iid in SERVICE_PRICE:
                if iid in existing_services:
                    continue  # don't buy the same service twice
                order = Order(client_id=client.id, item_type="service", item_id=iid,
                              amount_gbp=SERVICE_PRICE[iid], paid=True, status="active",
                              details=details if isinstance(details, dict) else {})
                SessionLocal.add(order)
                SessionLocal.flush()
                make_service_task(client, order, iid)
                existing_services.add(iid)
        recompute_docs(client)
        SessionLocal.commit()
        return jsonify(dashboard_payload(user))

    @app.post("/me/password")
    def my_password():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        old = data.get("old") or ""
        new = data.get("new") or ""
        if len(new) < 6:
            return jsonify({"error": "password too short", "code": "too_short"}), 400
        if user.password_hash and not verify_password(old, user.password_hash):
            return jsonify({"error": "wrong password", "code": "wrong_password"}), 400
        user.password_hash = hash_password(new)
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.post("/me/update")
    def my_update():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if name:
            user.name = name[:255]
            # keep the client record's display name in sync
            c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
            if c:
                c.name = user.name
        SessionLocal.commit()
        return jsonify(user.to_public())

    @app.delete("/me")
    def my_delete():
        user, err = require_user()
        if err:
            return err
        c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
        if c:
            _purge_client(c.id)
            SessionLocal.delete(c)
        _delete_user_sessions(user.id)
        SessionLocal.delete(user)
        SessionLocal.commit()
        return jsonify({"ok": True})

    def _session_row(s: Session, current_sid: int | None) -> dict:
        return {
            "id": s.id,
            "browser": s.browser or "Browser",
            "os": s.os or "Unknown",
            "device": s.device or "Desktop",
            "ip": s.ip or "",
            "current": s.id == current_sid,
            "createdAt": s.created_at.isoformat() if s.created_at else None,
            "lastSeenAt": s.last_seen_at.isoformat() if s.last_seen_at else None,
        }

    @app.get("/me/sessions")
    def my_sessions():
        user, err = require_user()
        if err:
            return err
        cur = current_sid()
        rows = SessionLocal.execute(
            select(Session)
            .where(Session.user_id == user.id, Session.revoked == False)  # noqa: E712
            .order_by(Session.last_seen_at.desc())
        ).scalars().all()
        return jsonify({"sessions": [_session_row(s, cur) for s in rows], "currentId": cur})

    @app.delete("/me/sessions/<int:sess_id>")
    def my_session_revoke(sess_id: int):
        user, err = require_user()
        if err:
            return err
        s = SessionLocal.get(Session, sess_id)
        if not s or s.user_id != user.id:
            return jsonify({"error": "not found"}), 404
        s.revoked = True
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.post("/me/sessions/revoke-others")
    def my_sessions_revoke_others():
        """Sign out every device except the one making this request."""
        user, err = require_user()
        if err:
            return err
        cur = current_sid()
        n = 0
        for s in SessionLocal.execute(
            select(Session).where(Session.user_id == user.id, Session.revoked == False)  # noqa: E712
        ).scalars().all():
            if s.id != cur:
                s.revoked = True
                n += 1
        SessionLocal.commit()
        return jsonify({"ok": True, "revoked": n})

    @app.post("/me/accept-terms")
    def my_accept_terms():
        user, err = require_user()
        if err:
            return err
        if not user.terms_accepted_at:
            user.terms_accepted_at = datetime.utcnow()
            SessionLocal.commit()
        return jsonify(user.to_public())

    @app.post("/me/locale")
    def my_locale():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        loc = (data.get("locale") or "").strip()
        if loc in ("ru", "en", "uz", "uz-cyrl"):
            user.locale = loc
            SessionLocal.commit()
        return jsonify(user.to_public())

    # ---- Link an email to the account (with a verification code) ----------
    @app.post("/me/email/start")
    def my_email_start():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            return jsonify({"error": "invalid email", "code": "invalid"}), 400
        other = SessionLocal.execute(
            select(User).where(User.email == email, User.id != user.id)
        ).scalar_one_or_none()
        if other:
            return jsonify({"error": "email taken", "code": "email_taken"}), 409
        code = gen_code()
        user.pending_email = email
        user.email_code = code
        user.email_code_expires = datetime.utcnow() + timedelta(minutes=15)
        SessionLocal.commit()
        mailer.send_code(email, code)
        return jsonify({"ok": True, "delivered": mailer.email_configured()})

    @app.post("/me/email/verify")
    def my_email_verify():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        code = (data.get("code") or "").strip()
        if not user.pending_email or not user.email_code:
            return jsonify({"error": "no pending email", "code": "no_pending"}), 400
        if user.email_code_expires and datetime.utcnow() > user.email_code_expires:
            return jsonify({"error": "code expired", "code": "expired"}), 400
        if code != user.email_code:
            return jsonify({"error": "wrong code", "code": "bad_code"}), 400
        other = SessionLocal.execute(
            select(User).where(User.email == user.pending_email, User.id != user.id)
        ).scalar_one_or_none()
        if other:
            return jsonify({"error": "email taken", "code": "email_taken"}), 409
        # A password lets the user actually sign in by email later (esp. if they
        # then unlink Telegram). Required when the account has no password yet.
        password = data.get("password") or ""
        if not user.password_hash:
            if len(password) < 6:
                return jsonify({"error": "password too short", "code": "weak_password"}), 400
            user.password_hash = hash_password(password)
        elif password and len(password) >= 6:
            user.password_hash = hash_password(password)
        user.email = user.pending_email
        user.email_verified = True
        user.pending_email = None
        user.email_code = None
        user.email_code_expires = None
        SessionLocal.commit()
        return jsonify(user.to_public())

    # ---- Reviews (after completing a package or a service) -----------------
    def _reviewable_order(user: User, order_id):
        """Return (client, order) for a completed order owned by the user; else
        (None, error_response). Works for both packages and services."""
        c = SessionLocal.execute(
            select(Client).where(Client.user_id == user.id)
        ).scalar_one_or_none()
        if not c:
            return None, (jsonify({"error": "not found"}), 404)
        o = SessionLocal.get(Order, int(order_id)) if order_id else None
        if not o or o.client_id != c.id:
            return None, (jsonify({"error": "not found"}), 404)
        return (c, o), None

    @app.post("/me/review")
    def my_review():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        res, rerr = _reviewable_order(user, data.get("orderId"))
        if rerr:
            return rerr
        c, o = res
        try:
            stars = max(1, min(5, int(data.get("stars") or 5)))
        except (TypeError, ValueError):
            stars = 5
        body = (data.get("text") or "").strip()[:2000]
        if not SessionLocal.execute(
            select(Review).where(Review.order_id == o.id)
        ).scalar_one_or_none():
            SessionLocal.add(Review(client_id=c.id, order_id=o.id, item_type=o.item_type,
                                    package_id=o.item_id, stars=stars, body=body))
        o.archived = True  # acknowledged — hides package card / moves service to history
        o.status = "done"
        SessionLocal.commit()
        return jsonify(dashboard_payload(user))

    @app.post("/me/review/skip")
    def my_review_skip():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        res, rerr = _reviewable_order(user, data.get("orderId"))
        if rerr:
            return rerr
        _, o = res
        o.archived = True
        o.status = "done"
        SessionLocal.commit()
        return jsonify(dashboard_payload(user))

    # ---- Edit arrival details (client) ------------------------------------
    ARRIVAL_FIELDS = ("arrivalDate", "arrivalTime", "airport", "flight")

    def mark_airport_meet_active(client, order):
        """Once arrival details exist, move the airport-meet step from 'todo' to
        'inProgress' so the operator board and the client cabinet both show it as
        in progress (the cabinet also shows a live countdown / "now")."""
        for t in client_tasks(client.id):
            if (t.kind == "step" and t.key == "airportMeet"
                    and (not order or t.order_id == order.id) and t.status == "todo"):
                t.status = "inProgress"

    @app.post("/me/arrival")
    def my_arrival():
        user, err = require_user()
        if err:
            return err
        c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
        if not c:
            return jsonify({"error": "not found"}), 404
        orders = client_orders(c.id)
        pkg = next((o for o in reversed(orders) if o.item_type == "package" and not o.archived), None)
        if not pkg:
            return jsonify({"error": "no package"}), 404
        data = request.get_json(silent=True) or {}
        details = dict(pkg.details or {})
        for k in ARRIVAL_FIELDS:
            if k in data:
                details[k] = (str(data.get(k) or "")).strip()[:120]
        pkg.details = details
        if details.get("arrivalDate"):
            mark_airport_meet_active(c, pkg)
        SessionLocal.commit()
        return jsonify(dashboard_payload(user))

    # ---- Housing shortlist (client) ---------------------------------------
    @app.post("/me/housing")
    def my_housing_add():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        source = "catalog" if data.get("source") == "catalog" else "link"
        ref = (data.get("ref") or "").strip()[:512]
        if not ref:
            return jsonify({"error": "empty"}), 400
        try:
            price = int(data.get("priceGBP") or 0)
        except (TypeError, ValueError):
            price = 0
        c = get_or_create_client(user)
        # avoid duplicates of the same catalog item / link
        existing = SessionLocal.execute(
            select(HousingItem).where(HousingItem.client_id == c.id, HousingItem.ref == ref)
        ).scalar_one_or_none()
        if existing:
            return jsonify(housing_row(existing)), 200

        # Real details: catalog → the listing; link → scrape OpenGraph tags.
        photo = None
        desc = ""
        title = (data.get("title") or "").strip()[:255]
        addr = (data.get("addr") or "").strip()[:255]
        if source == "catalog" and ref.startswith("catalog:"):
            try:
                listing = SessionLocal.get(Listing, int(ref.split(":", 1)[1]))
                if listing:
                    photo = listing.photo_url
                    if not price:
                        price = listing.price_gbp
                    if not addr:
                        addr = listing.addr
            except (TypeError, ValueError):
                pass
        elif source == "link":
            meta = fetch_og_meta(ref)
            photo = meta.get("photo")
            desc = meta.get("description", "")
            if meta.get("title"):
                title = meta["title"]
            if not price and meta.get("price"):
                price = meta["price"]

        h = HousingItem(
            client_id=c.id, source=source, ref=ref,
            title=title, description=desc, price_gbp=price,
            addr=addr, photo_url=photo, status="new",
        )
        SessionLocal.add(h)
        SessionLocal.commit()
        return jsonify(housing_row(h)), 201

    @app.delete("/me/housing/<int:item_id>")
    def my_housing_delete(item_id: int):
        user, err = require_user()
        if err:
            return err
        c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
        h = SessionLocal.get(HousingItem, item_id)
        if not c or not h or h.client_id != c.id:
            return jsonify({"error": "not found"}), 404
        SessionLocal.delete(h)
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.post("/me/housing/<int:item_id>/viewing")
    def my_housing_viewing(item_id: int):
        """Request (and pay £30 for) an accompanied viewing of a shortlisted
        property. Creates a paid `viewing` order the operator then schedules."""
        user, err = require_user()
        if err:
            return err
        c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
        h = SessionLocal.get(HousingItem, item_id)
        if not c or not h or h.client_id != c.id:
            return jsonify({"error": "not found"}), 404
        # One paid viewing per property — return the existing one if already requested.
        existing = SessionLocal.execute(
            select(Order).where(
                Order.client_id == c.id,
                Order.item_type == "viewing",
                Order.item_id == str(h.id),
            )
        ).scalar_one_or_none()
        if existing:
            return jsonify(housing_row(h)), 200
        order = Order(
            client_id=c.id, item_type="viewing", item_id=str(h.id),
            amount_gbp=VIEWING_PRICE, paid=True, status="active",
            details={"housingId": h.id, "addr": h.addr or h.title},
        )
        SessionLocal.add(order)
        SessionLocal.commit()
        addr = h.title or h.addr or "квартира"
        notify_client(c, "housing_status", addr=addr, status_key=h.status)
        return jsonify(housing_row(h)), 201

    # ---- Client ↔ manager chat --------------------------------------------
    def message_row(m: Message) -> dict:
        return {
            "id": m.id,
            "sender": m.sender,
            "channel": m.channel,
            "author": m.author_name,
            "body": m.body,
            "createdAt": m.created_at.isoformat(),
        }

    def client_messages(client_id: int, channel: str = "manager"):
        return SessionLocal.execute(
            select(Message)
            .where(Message.client_id == client_id, Message.channel == channel)
            .order_by(Message.id)
        ).scalars().all()

    def _chat_preview(body: str) -> str:
        s = " ".join((body or "").split())
        return (s[:80] + "…") if len(s) > 80 else s

    def _channel_arg(default: str = "manager") -> str:
        ch = (request.args.get("channel") or (request.get_json(silent=True) or {}).get("channel") or default)
        return "runner" if ch == "runner" else "manager"

    @app.get("/me/messages")
    def my_messages():
        user, err = require_user()
        if err:
            return err
        c = SessionLocal.execute(select(Client).where(Client.user_id == user.id)).scalar_one_or_none()
        if not c:
            return jsonify({"messages": []})
        return jsonify({"messages": [message_row(m) for m in client_messages(c.id, _channel_arg())]})

    @app.post("/me/messages")
    def my_send_message():
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        body = (data.get("body") or "").strip()
        if not body:
            return jsonify({"error": "empty"}), 400
        channel = _channel_arg()
        c = get_or_create_client(user)
        m = Message(client_id=c.id, sender="client", channel=channel,
                    author_name=user.name or "Client", body=body[:4000])
        SessionLocal.add(m)
        SessionLocal.commit()
        # Notify the counterpart on their Telegram (best-effort).
        peer_id = c.runner_id if channel == "runner" else c.manager_id
        if peer_id:
            peer = SessionLocal.get(User, peer_id)
            if peer:
                notify.send(peer, "chat_message", name=(user.name or "Клиент"),
                            preview=_chat_preview(body))
        return jsonify(message_row(m)), 201

    @app.get("/admin/clients/<int:client_id>/messages")
    def admin_messages(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        return jsonify({"messages": [message_row(m) for m in client_messages(client_id, "manager")]})

    @app.post("/admin/clients/<int:client_id>/messages")
    def admin_send_message(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        body = (data.get("body") or "").strip()
        if not body:
            return jsonify({"error": "empty"}), 400
        m = Message(client_id=c.id, sender="manager", channel="manager",
                    author_name=user.name or "Manager", body=body[:4000])
        SessionLocal.add(m)
        SessionLocal.commit()
        notify_client(c, "chat_message", name=(user.name or "Менеджер"), preview=_chat_preview(body))
        return jsonify(message_row(m)), 201

    # ---- Runner ↔ client chat ---------------------------------------------
    @app.get("/runner/clients")
    def runner_clients():
        """Clients assigned to this runner — so they can open a chat with each."""
        user, err = require_role("runner")
        if err:
            return err
        rows = SessionLocal.execute(
            select(Client).where(Client.runner_id == user.id).order_by(Client.id)
        ).scalars().all()
        out = []
        for c in rows:
            u = SessionLocal.get(User, c.user_id) if c.user_id else None
            out.append({
                "id": c.id,
                "name": c.name or (u.name if u else "") or "Клиент",
                "photoUrl": (u.photo_url if u else None),
            })
        return jsonify({"clients": out})

    def _runner_client(user: User, client_id: int) -> Client | None:
        c = SessionLocal.get(Client, client_id)
        return c if (c and c.runner_id == user.id) else None

    @app.get("/runner/clients/<int:client_id>/messages")
    def runner_messages(client_id: int):
        user, err = require_role("runner")
        if err:
            return err
        c = _runner_client(user, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        return jsonify({"messages": [message_row(m) for m in client_messages(c.id, "runner")]})

    @app.post("/runner/clients/<int:client_id>/messages")
    def runner_send_message(client_id: int):
        user, err = require_role("runner")
        if err:
            return err
        c = _runner_client(user, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        body = (data.get("body") or "").strip()
        if not body:
            return jsonify({"error": "empty"}), 400
        m = Message(client_id=c.id, sender="runner", channel="runner",
                    author_name=user.name or "Runner", body=body[:4000])
        SessionLocal.add(m)
        SessionLocal.commit()
        notify_client(c, "chat_message", name=(user.name or "Сопровождающий"), preview=_chat_preview(body))
        return jsonify(message_row(m)), 201

    # ---- Operator console --------------------------------------------------
    def admin_client_row(c: Client, runners: dict, managers: dict) -> dict:
        orders = client_orders(c.id)
        # Active (non-archived) package only — otherwise completed packages' steps leak in.
        pkg = next(
            (o for o in reversed(orders) if o.item_type == "package" and not o.archived), None
        )
        svc = [o for o in orders if o.item_type == "service"]
        tasks = client_tasks(c.id)
        step_tasks = [t for t in tasks if t.kind == "step" and pkg and t.order_id == pkg.id]
        # Per-order (not per-key) so a re-bought service resolves to its own task.
        svc_task_by_order = {t.order_id: t for t in tasks if t.kind == "service" and t.order_id}
        u = SessionLocal.get(User, c.user_id) if c.user_id else None
        idx = active_step_index(step_tasks) if step_tasks else 0
        all_paid = all(o.paid for o in orders) if orders else True
        steps_done = bool(step_tasks) and all(t.status == "done" for t in step_tasks)
        active = any(t.status != "done" for t in tasks)
        attach_map = order_attachments([o.id for o in svc])
        step_att = task_attachments([t.id for t in step_tasks])

        def _svc_done(o: Order) -> bool:
            st = svc_task_by_order.get(o.id)
            return bool(st and st.status == "done")

        # First not-yet-done service — for the "one at a time" active board display.
        active_service = next((o.item_id for o in svc if not _svc_done(o)), None)
        # Full purchase history (every order, with per-step completion times) — so
        # the operator keeps a record of what a finished client bought and when
        # each part was completed, even after the package is archived.
        steps_by_order: dict = {}
        for t in tasks:
            if t.kind == "step" and t.order_id:
                steps_by_order.setdefault(t.order_id, []).append(t)

        def _iso(dt):
            # Mark as UTC so the browser renders it in the operator's local time.
            return dt.isoformat() + "Z" if dt else None

        history = []
        for o in orders:
            item = {
                "type": o.item_type,
                "id": o.item_id,
                "amountGBP": o.amount_gbp,
                "paid": o.paid,
                "createdAt": _iso(o.created_at),
            }
            if o.item_type == "package":
                osteps = sorted(steps_by_order.get(o.id, []), key=lambda x: (x.position, x.id))
                item["steps"] = [
                    {"key": s.key, "status": s.status, "completedAt": _iso(s.completed_at)}
                    for s in osteps
                ]
                done = bool(osteps) and all(s.status == "done" for s in osteps)
                comp = [s.completed_at for s in osteps if s.completed_at]
                item["status"] = "done" if done else "active"
                item["completedAt"] = _iso(max(comp)) if (done and comp) else None
            else:
                # Services resolve to their per-order task; a viewing order has none.
                st = svc_task_by_order.get(o.id)
                done = bool(st and st.status == "done")
                item["status"] = "done" if done else "active"
                item["completedAt"] = _iso(st.completed_at) if (st and done) else None
            history.append(item)
        return {
            "id": c.id,
            "name": c.name,
            "package": pkg.item_id if pkg else None,
            "amount": sum(o.amount_gbp for o in orders),
            "stepIndex": idx,
            "stepTotal": len(step_tasks),
            "hasPackage": pkg is not None,
            "packageOrderId": pkg.id if pkg else None,
            "packageComplete": steps_done,
            "packageDetails": (pkg.details or {}) if pkg else {},
            "hasServices": len(svc) > 0,
            "active": active,
            "completed": bool(orders) and not active,
            "steps": [
                {
                    "taskId": t.id,
                    "key": t.key,
                    "status": t.status,
                    "canUpload": t.key in FILE_STEPS,
                    "attachments": step_att.get(t.id, []),
                }
                for t in step_tasks
            ],
            "activeService": active_service,
            "services": [
                {
                    "id": o.item_id,
                    "orderId": o.id,
                    "paid": o.paid,
                    "taskId": svc_task_by_order[o.id].id if o.id in svc_task_by_order else None,
                    "status": svc_task_by_order[o.id].status if o.id in svc_task_by_order else "todo",
                    "done": _svc_done(o),
                    "attachments": attach_map.get(o.id, []),
                }
                for o in svc
            ],
            "housing": housing_rows(client_housing(c.id)),
            "history": history,
            "runner": runners.get(c.runner_id),
            "runnerId": c.runner_id,
            "manager": managers.get(c.manager_id),
            "managerId": c.manager_id,
            "paid": all_paid,
            "photoUrl": u.photo_url if u else None,
            "email": u.email if u else None,
            "telegram": u.telegram_username if u else None,
            "phone": u.phone if u else None,
        }

    @app.get("/admin/overview")
    def admin_overview():
        user, err = require_role("operator")
        if err:
            return err
        clients = SessionLocal.execute(select(Client).order_by(Client.id)).scalars().all()
        runners = runner_name_map()
        managers = manager_name_map()
        rows = [admin_client_row(c, runners, managers) for c in clients]
        all_orders = SessionLocal.execute(select(Order)).scalars().all()
        awaiting = sum(o.amount_gbp for o in all_orders if not o.paid)
        open_tasks = SessionLocal.execute(
            select(Task).where(Task.status != "done", Task.time != "")
        ).scalars().all()
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        active_clients = sum(
            1 for c in clients if any(t.status != "done" for t in client_tasks(c.id))
        )
        new_week = sum(1 for c in clients if c.created_at and c.created_at >= week_ago)
        attention = []
        for r in rows:
            if not r["managerId"]:
                attention.append({"id": f"nm{r['id']}", "type": "noManager", "who": r["name"], "clientId": r["id"]})
        for r in rows:
            if r["package"] and not r["runnerId"]:
                attention.append({"id": f"nr{r['id']}", "type": "noRunner", "who": r["name"], "clientId": r["id"]})
        for r in rows:
            if not r["paid"]:
                attention.append({"id": f"ap{r['id']}", "type": "awaitingPayment", "who": r["name"], "clientId": r["id"]})
        return jsonify(
            {
                "kpis": {
                    "activeClients": active_clients,
                    "tasksToday": len(open_tasks),
                    "awaitingPayment": awaiting,
                    "newWeek": new_week,
                },
                "clients": rows,
                "attention": attention,
                "runners": [{"id": rid, "name": nm} for rid, nm in runners.items()],
                "managers": [{"id": u.id, "name": u.name} for u in manager_users()],
            }
        )

    @app.post("/admin/clients/<int:client_id>/assign-runner")
    def admin_assign_runner(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        # key present (may be null) → set exactly; key absent → auto-pick first runner
        if "runner_id" in data:
            runner_id = data["runner_id"]
        else:
            first = SessionLocal.execute(
                select(User).where(User.role == "runner").order_by(User.id)
            ).scalars().first()
            runner_id = first.id if first else None
        c.runner_id = runner_id
        # Propagate to the client's field tasks that aren't done yet.
        for t in client_tasks(c.id):
            if t.status != "done" and (
                (t.kind == "step" and t.key in RUNNER_STEPS)
                or (t.kind == "service" and t.key in RUNNER_SERVICES)
            ):
                t.runner_id = runner_id
        SessionLocal.commit()
        if runner_id:
            names = runner_name_map()
            notify_client(c, "runner_assigned", name=names.get(runner_id, ""))
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.post("/admin/clients/<int:client_id>/assign-manager")
    def admin_assign_manager(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        # key present (may be null) → set exactly; key absent → acting operator takes it
        manager_id = data["manager_id"] if "manager_id" in data else user.id
        c.manager_id = manager_id
        SessionLocal.commit()
        if manager_id:
            names = manager_name_map()
            notify_client(c, "manager_assigned", name=names.get(manager_id, ""))
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.post("/admin/tasks/<int:task_id>/status")
    def admin_task_status(task_id: int):
        user, err = require_role("operator")
        if err:
            return err
        t = SessionLocal.get(Task, task_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        status = data.get("status")
        # onWay/arrived = runner field-visit stages; inProgress = a non-runner step
        # actively being worked (so the parallel cabinet path can show it "in progress").
        if status not in ("todo", "inProgress", "onWay", "arrived", "done"):
            return jsonify({"error": "bad status"}), 400
        was_done = t.status == "done"
        t.status = status
        if status == "done":
            if not was_done:
                t.completed_at = datetime.utcnow()
        else:
            t.completed_at = None  # reopened — drop the completion timestamp
        SessionLocal.commit()
        c = SessionLocal.get(Client, t.client_id)
        if status == "done" and not was_done:
            notify_task_done(c, t)
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    # ---- Operator: manage a client's packages / services ------------------
    def _row(c):
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.post("/admin/clients/<int:client_id>/package")
    def admin_set_package(client_id: int):
        """Set / change / upgrade the client's active package."""
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        pkg = d.get("packageId")
        if pkg not in PACKAGE_AMOUNT:
            return jsonify({"error": "bad package"}), 400
        paid = bool(d.get("paid", True))
        # Carry over arrival details from the package being replaced.
        details = {}
        for o in list(client_orders(c.id)):
            if o.item_type == "package" and not o.archived:
                details = dict(o.details or {})
                delete_order(o)
        SessionLocal.flush()
        order = Order(client_id=c.id, item_type="package", item_id=pkg,
                      amount_gbp=PACKAGE_AMOUNT[pkg], paid=paid,
                      status="active" if paid else "new", details=details)
        SessionLocal.add(order)
        SessionLocal.flush()
        make_package_tasks(c, order, pkg)
        recompute_docs(c)
        SessionLocal.commit()
        return _row(c)

    @app.post("/admin/clients/<int:client_id>/service")
    def admin_add_service(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        sid = d.get("serviceId")
        if sid not in SERVICE_PRICE:
            return jsonify({"error": "bad service"}), 400
        if sid in in_progress_service_ids(c.id):
            return jsonify({"error": "already added", "code": "dup"}), 409
        paid = bool(d.get("paid", True))
        order = Order(client_id=c.id, item_type="service", item_id=sid,
                      amount_gbp=SERVICE_PRICE[sid], paid=paid,
                      status="active" if paid else "new", details={})
        SessionLocal.add(order)
        SessionLocal.flush()
        make_service_task(c, order, sid)
        recompute_docs(c)
        SessionLocal.commit()
        return _row(c)

    @app.delete("/admin/orders/<int:order_id>")
    def admin_delete_order(order_id: int):
        """Remove a package or a service from a client (fixes accidental purchases)."""
        user, err = require_role("operator")
        if err:
            return err
        o = SessionLocal.get(Order, order_id)
        if not o:
            return jsonify({"error": "not found"}), 404
        c = SessionLocal.get(Client, o.client_id)
        delete_order(o)
        if c:
            recompute_docs(c)
        SessionLocal.commit()
        return _row(c) if c else jsonify({"ok": True})

    @app.post("/admin/clients/<int:client_id>/arrival")
    def admin_set_arrival(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        pkg = next((o for o in reversed(client_orders(c.id))
                    if o.item_type == "package" and not o.archived), None)
        if not pkg:
            return jsonify({"error": "no package"}), 404
        d = request.get_json(silent=True) or {}
        details = dict(pkg.details or {})
        for k in ("arrivalDate", "arrivalTime", "airport", "flight"):
            if k in d:
                details[k] = (str(d.get(k) or "")).strip()[:120]
        pkg.details = details
        if details.get("arrivalDate"):
            mark_airport_meet_active(c, pkg)
        SessionLocal.commit()
        return _row(c)

    @app.post("/admin/clients/<int:client_id>/update")
    def admin_client_update(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if name:
            c.name = name[:255]
            if c.user_id:
                u = SessionLocal.get(User, c.user_id)
                if u:
                    u.name = c.name
        SessionLocal.commit()
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    # ---- Account / team management (operator) ------------------------------
    MANAGEABLE_ROLES = {"client", "operator", "agency", "runner", "admin"}

    def account_row(u: User) -> dict:
        row = {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "active": u.is_active,
            "telegram": u.telegram_username,
            "phone": u.phone,
            "photoUrl": u.photo_url,
            "createdAt": u.created_at.isoformat() if u.created_at else None,
        }
        if u.role == "runner":
            rtasks = SessionLocal.execute(
                select(Task).where(Task.runner_id == u.id)
            ).scalars().all()
            done = [t for t in rtasks if t.status == "done"]
            unpaid = [t for t in done if not t.runner_paid]
            row["taskTotal"] = len(rtasks)
            row["taskDone"] = len(done)
            # Payout: fee per completed visit; owed = completed-but-unpaid.
            row["visitFee"] = RUNNER_VISIT_FEE
            row["visitsDone"] = len(done)
            row["visitsUnpaid"] = len(unpaid)
            row["owedGBP"] = len(unpaid) * RUNNER_VISIT_FEE
            row["clientCount"] = SessionLocal.execute(
                select(func.count()).select_from(Client).where(Client.runner_id == u.id)
            ).scalar_one()
        if u.role == "client":
            cl = SessionLocal.execute(
                select(Client).where(Client.user_id == u.id)
            ).scalar_one_or_none()
            if cl:
                orders = client_orders(cl.id)
                pkg = next(
                    (o for o in reversed(orders) if o.item_type == "package" and not o.archived),
                    None,
                )
                row["clientId"] = cl.id
                row["package"] = pkg.item_id if pkg else None
                row["paid"] = all(o.paid for o in orders) if orders else True
        return row

    @app.get("/admin/accounts")
    def admin_accounts():
        user, err = require_role("operator")
        if err:
            return err
        users = SessionLocal.execute(select(User).order_by(User.role, User.id)).scalars().all()
        return jsonify({"accounts": [account_row(u) for u in users]})

    # ---- Runner detail + payouts (operator) -------------------------------
    @app.get("/admin/runners/<int:runner_id>")
    def admin_runner_detail(runner_id: int):
        user, err = require_role("operator")
        if err:
            return err
        u = SessionLocal.get(User, runner_id)
        if not u or u.role != "runner":
            return jsonify({"error": "not found"}), 404
        names = client_name_map()

        def _iso(dt):
            return dt.isoformat() + "Z" if dt else None

        tasks = SessionLocal.execute(
            select(Task).where(Task.runner_id == u.id).order_by(Task.position, Task.id)
        ).scalars().all()

        # Group the runner's field visits by client.
        by_client: dict = {}
        for t in tasks:
            by_client.setdefault(t.client_id, []).append(t)

        clients = []
        for c in SessionLocal.execute(
            select(Client).where(Client.runner_id == u.id).order_by(Client.id)
        ).scalars().all():
            ct = by_client.pop(c.id, [])
            clients.append({
                "id": c.id,
                "name": names.get(c.id, c.name or ""),
                "tasks": [{
                    "id": t.id, "kind": t.kind, "key": t.key, "status": t.status,
                    "time": t.time, "addr": t.addr,
                    "completedAt": _iso(t.completed_at), "runnerPaid": t.runner_paid,
                } for t in ct],
            })
        # Any leftover tasks whose client is no longer assigned to this runner.
        for cid, ct in by_client.items():
            clients.append({
                "id": cid, "name": names.get(cid, ""),
                "tasks": [{
                    "id": t.id, "kind": t.kind, "key": t.key, "status": t.status,
                    "time": t.time, "addr": t.addr,
                    "completedAt": _iso(t.completed_at), "runnerPaid": t.runner_paid,
                } for t in ct],
            })

        done = [t for t in tasks if t.status == "done"]
        unpaid = [t for t in done if not t.runner_paid]
        return jsonify({
            "runner": account_row(u),
            "clients": clients,
            "payout": {
                "visitFee": RUNNER_VISIT_FEE,
                "visitsDone": len(done),
                "visitsUnpaid": len(unpaid),
                "owedGBP": len(unpaid) * RUNNER_VISIT_FEE,
                "paidGBP": (len(done) - len(unpaid)) * RUNNER_VISIT_FEE,
            },
        })

    @app.post("/admin/tasks/<int:task_id>/runner-paid")
    def admin_task_runner_paid(task_id: int):
        user, err = require_role("operator")
        if err:
            return err
        t = SessionLocal.get(Task, task_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        t.runner_paid = bool(d.get("paid", True))
        SessionLocal.commit()
        return jsonify({"ok": True, "id": t.id, "runnerPaid": t.runner_paid})

    @app.post("/admin/runners/<int:runner_id>/pay-all")
    def admin_runner_pay_all(runner_id: int):
        """Mark every completed-but-unpaid visit for this runner as paid."""
        user, err = require_role("operator")
        if err:
            return err
        u = SessionLocal.get(User, runner_id)
        if not u or u.role != "runner":
            return jsonify({"error": "not found"}), 404
        n = 0
        for t in SessionLocal.execute(
            select(Task).where(Task.runner_id == u.id, Task.status == "done", Task.runner_paid == False)  # noqa: E712
        ).scalars().all():
            t.runner_paid = True
            n += 1
        SessionLocal.commit()
        return jsonify({"ok": True, "paid": n})

    @app.post("/admin/accounts")
    def admin_create_account():
        user, err = require_role("operator")
        if err:
            return err
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()
        role = d.get("role") or "runner"
        email = (d.get("email") or "").strip().lower() or None
        password = d.get("password") or ""
        if not name or role not in MANAGEABLE_ROLES:
            return jsonify({"error": "missing_fields"}), 400
        if email and SessionLocal.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none():
            return jsonify({"error": "email already registered", "code": "email_taken"}), 409
        tg = (d.get("telegram") or "").strip().lstrip("@") or None
        u = User(
            name=name[:255],
            email=email,
            role=role,
            phone=(d.get("phone") or "").strip() or None,
            telegram_username=tg,
            password_hash=hash_password(password) if password else None,
            terms_accepted_at=datetime.utcnow(),
        )
        SessionLocal.add(u)
        SessionLocal.commit()
        return jsonify(account_row(u)), 201

    @app.patch("/admin/accounts/<int:uid>")
    def admin_update_account(uid: int):
        user, err = require_role("operator")
        if err:
            return err
        u = SessionLocal.get(User, uid)
        if not u:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()
        if name:
            u.name = name[:255]
            cl = SessionLocal.execute(
                select(Client).where(Client.user_id == u.id)
            ).scalar_one_or_none()
            if cl:
                cl.name = u.name
        if d.get("role") in MANAGEABLE_ROLES:
            u.role = d["role"]
        if "email" in d:
            email = (d.get("email") or "").strip().lower() or None
            if email != u.email:
                if email and SessionLocal.execute(
                    select(User).where(User.email == email, User.id != u.id)
                ).scalar_one_or_none():
                    return jsonify({"error": "email taken", "code": "email_taken"}), 409
                u.email = email
        if "phone" in d:
            u.phone = (d.get("phone") or "").strip() or None
        if "telegram" in d:
            u.telegram_username = (d.get("telegram") or "").strip().lstrip("@") or None
        if "active" in d and uid != user.id:  # can't lock yourself out
            u.is_active = bool(d["active"])
            if not u.is_active:
                _revoke_user_sessions(u.id)  # deactivation logs the user out everywhere
        if d.get("password"):
            u.password_hash = hash_password(d["password"])
        SessionLocal.commit()
        return jsonify(account_row(u))

    @app.delete("/admin/accounts/<int:uid>")
    def admin_delete_account(uid: int):
        user, err = require_role("operator")
        if err:
            return err
        if uid == user.id:
            return jsonify({"error": "cannot delete yourself", "code": "self"}), 400
        u = SessionLocal.get(User, uid)
        if not u:
            return jsonify({"error": "not found"}), 404
        # Detach references so we don't leave dangling FKs.
        SessionLocal.execute(
            Client.__table__.update().where(Client.manager_id == uid).values(manager_id=None)
        )
        SessionLocal.execute(
            Client.__table__.update().where(Client.runner_id == uid).values(runner_id=None)
        )
        SessionLocal.execute(
            Task.__table__.update().where(Task.runner_id == uid).values(runner_id=None)
        )
        # If this user is a client, remove their whole relocation record.
        cl = SessionLocal.execute(
            select(Client).where(Client.user_id == uid)
        ).scalar_one_or_none()
        if cl:
            _purge_client(cl.id)
            SessionLocal.delete(cl)
        SessionLocal.execute(Listing.__table__.delete().where(Listing.agency_id == uid))
        _delete_user_sessions(uid)
        SessionLocal.delete(u)
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.delete("/admin/clients/<int:client_id>")
    def admin_delete_client(client_id: int):
        user, err = require_role("operator")
        if err:
            return err
        c = SessionLocal.get(Client, client_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        uid = c.user_id
        _purge_client(c.id)
        SessionLocal.delete(c)
        if uid and uid != user.id:
            u = SessionLocal.get(User, uid)
            if u:
                _delete_user_sessions(uid)
                SessionLocal.delete(u)
        SessionLocal.commit()
        return jsonify({"ok": True})

    # ---- Profile photo upload (operator) ----------------------------------
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ALLOWED_IMG = {"jpg", "jpeg", "png", "webp", "gif"}

    @app.post("/admin/accounts/<int:uid>/photo")
    def admin_account_photo(uid: int):
        user, err = require_role("operator")
        if err:
            return err
        u = SessionLocal.get(User, uid)
        if not u:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_IMG:
            return jsonify({"error": "bad type", "code": "bad_type"}), 400
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        u.photo_url = f"/api/uploads/{name}"
        SessionLocal.commit()
        return jsonify(account_row(u))

    @app.get("/uploads/<path:name>")
    def serve_upload(name: str):
        return send_from_directory(UPLOAD_DIR, name)

    # ---- Reviews (operator) -----------------------------------------------
    @app.get("/admin/reviews")
    def admin_reviews():
        user, err = require_role("operator")
        if err:
            return err
        revs = SessionLocal.execute(select(Review).order_by(Review.id.desc())).scalars().all()
        names = client_name_map()
        rows = [
            {
                "id": r.id,
                "clientId": r.client_id,
                "clientName": names.get(r.client_id, ""),
                "itemType": r.item_type,
                "itemId": r.package_id,
                "stars": r.stars,
                "body": r.body,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in revs
        ]
        avg = round(sum(r.stars for r in revs) / len(revs), 1) if revs else 0
        return jsonify({"reviews": rows, "count": len(revs), "avg": avg})

    # ---- Payments (operator) ----------------------------------------------
    def payment_row(o: Order) -> dict:
        names = client_name_map()
        return {
            "id": o.id,
            "clientId": o.client_id,
            "clientName": names.get(o.client_id, ""),
            "itemType": o.item_type,
            "itemId": o.item_id,
            "amountGBP": o.amount_gbp,
            "paid": o.paid,
            "status": o.status,
            "createdAt": o.created_at.isoformat() if o.created_at else None,
        }

    @app.get("/admin/payments")
    def admin_payments():
        user, err = require_role("operator")
        if err:
            return err
        orders = SessionLocal.execute(select(Order).order_by(Order.id.desc())).scalars().all()
        return jsonify(
            {
                "orders": [payment_row(o) for o in orders],
                "totals": {
                    "paid": sum(o.amount_gbp for o in orders if o.paid),
                    "unpaid": sum(o.amount_gbp for o in orders if not o.paid and o.status != "refunded"),
                    "refunded": sum(o.amount_gbp for o in orders if o.status == "refunded"),
                    "count": len(orders),
                },
            }
        )

    @app.post("/admin/orders/<int:order_id>/paid")
    def admin_order_paid(order_id: int):
        user, err = require_role("operator")
        if err:
            return err
        o = SessionLocal.get(Order, order_id)
        if not o:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        was_paid = o.paid
        o.paid = bool(d.get("paid", True))
        if o.paid and o.status == "new":
            o.status = "active"
        SessionLocal.commit()
        if o.paid and not was_paid:
            notify_client(SessionLocal.get(Client, o.client_id), "order_paid")
        return jsonify(payment_row(o))

    @app.post("/admin/orders/<int:order_id>/refund")
    def admin_order_refund(order_id: int):
        """Mark an order refunded (unpaid + refunded status). Payme refund is
        triggered separately once real payments are wired."""
        user, err = require_role("operator")
        if err:
            return err
        o = SessionLocal.get(Order, order_id)
        if not o:
            return jsonify({"error": "not found"}), 404
        o.paid = False
        o.status = "refunded"
        SessionLocal.commit()
        notify_client(SessionLocal.get(Client, o.client_id), "order_refunded")
        return jsonify(payment_row(o))

    # ---- Housing shortlist (operator) -------------------------------------
    @app.post("/admin/housing/<int:item_id>/status")
    def admin_housing_status(item_id: int):
        user, err = require_role("operator")
        if err:
            return err
        h = SessionLocal.get(HousingItem, item_id)
        if not h:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        status = d.get("status")
        if status not in HOUSING_STATUSES:
            return jsonify({"error": "bad status"}), 400
        h.status = status
        if "note" in d:
            h.note = (d.get("note") or "").strip()[:512]
        if "viewingAt" in d:
            h.viewing_at = (d.get("viewingAt") or "").strip()[:64]
        SessionLocal.commit()
        c = SessionLocal.get(Client, h.client_id)
        addr = h.title or h.addr or "квартира"
        if status == "viewing" and h.viewing_at:
            notify_client(c, "housing_viewing", addr=addr, when=h.viewing_at.replace("T", " "))
        else:
            notify_client(c, "housing_status", addr=addr, status_key=status)
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.post("/admin/housing/<int:item_id>/media")
    def admin_housing_media_upload(item_id: int):
        user, err = require_role("operator")
        if err:
            return err
        h = SessionLocal.get(HousingItem, item_id)
        if not h:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "bin"
        kind = "video" if ext in ("mp4", "mov", "webm", "m4v") else "image"
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        SessionLocal.add(HousingMedia(
            housing_id=h.id, client_id=h.client_id,
            url=f"/api/uploads/{name}", filename=f.filename[:255], kind=kind,
        ))
        SessionLocal.commit()
        c = SessionLocal.get(Client, h.client_id)
        notify_client(c, "housing_media", addr=h.title or h.addr or "квартира")
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.delete("/admin/housing/media/<int:media_id>")
    def admin_housing_media_delete(media_id: int):
        user, err = require_role("operator")
        if err:
            return err
        m = SessionLocal.get(HousingMedia, media_id)
        if not m:
            return jsonify({"error": "not found"}), 404
        cid = m.client_id
        SessionLocal.delete(m)
        SessionLocal.commit()
        c = SessionLocal.get(Client, cid)
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    # ---- Service file attachments (operator) ------------------------------
    @app.post("/admin/orders/<int:order_id>/attachment")
    def admin_order_attachment(order_id: int):
        user, err = require_role("operator")
        if err:
            return err
        o = SessionLocal.get(Order, order_id)
        if not o:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "bin"
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        a = Attachment(order_id=o.id, client_id=o.client_id,
                       filename=f.filename[:255], url=f"/api/uploads/{name}")
        SessionLocal.add(a)
        SessionLocal.commit()
        c = SessionLocal.get(Client, o.client_id)
        notify_client(c, "file_uploaded")
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.post("/admin/tasks/<int:task_id>/attachment")
    def admin_task_attachment(task_id: int):
        user, err = require_role("operator")
        if err:
            return err
        t = SessionLocal.get(Task, task_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "bin"
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        a = Attachment(task_id=t.id, client_id=t.client_id,
                       filename=f.filename[:255], url=f"/api/uploads/{name}")
        SessionLocal.add(a)
        SessionLocal.commit()
        c = SessionLocal.get(Client, t.client_id)
        notify_client(c, "file_uploaded")
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    @app.delete("/admin/attachments/<int:att_id>")
    def admin_attachment_delete(att_id: int):
        user, err = require_role("operator")
        if err:
            return err
        a = SessionLocal.get(Attachment, att_id)
        if not a:
            return jsonify({"error": "not found"}), 404
        cid = a.client_id
        SessionLocal.delete(a)
        SessionLocal.commit()
        c = SessionLocal.get(Client, cid)
        return jsonify(admin_client_row(c, runner_name_map(), manager_name_map()))

    # ---- Agency ------------------------------------------------------------
    def _clean_amenities(raw) -> list[str]:
        """Normalise an amenities list from client JSON — short, de-duplicated slugs."""
        if not isinstance(raw, list):
            return []
        out: list[str] = []
        for a in raw:
            s = str(a).strip()[:32]
            if s and s not in out:
                out.append(s)
            if len(out) >= 20:
                break
        return out

    def listing_row(l: Listing) -> dict:
        return {
            "id": l.id,
            "priceGBP": l.price_gbp,
            "addr": l.addr,
            "area": l.area,
            "rooms": l.rooms,
            "baths": l.baths,
            "furnished": l.furnished,
            "status": l.status,
            "matches": l.matches,
            "photoUrl": l.photo_url,
            "photos": listing_gallery(l),
            "propertyType": l.property_type or "flat",
            "description": l.description or "",
            "amenities": l.amenities or [],
            "availableFrom": l.available_from or "",
            "depositGBP": l.deposit_gbp or 0,
        }

    def listing_gallery(l: Listing) -> list[str]:
        """Cover first, then the extra gallery photos (de-duplicated)."""
        out: list[str] = []
        if l.photo_url:
            out.append(l.photo_url)
        for p in (l.photos or []):
            if p and p not in out:
                out.append(p)
        return out

    def listing_card(l: Listing) -> dict:
        """Compact row for catalog grids (search page, agency)."""
        return {
            "id": l.id,
            "priceGBP": l.price_gbp,
            "addr": l.addr,
            "area": l.area,
            "rooms": l.rooms,
            "baths": l.baths,
            "furnished": l.furnished,
            "photoUrl": l.photo_url,
            "propertyType": l.property_type or "flat",
        }

    def listing_detail(l: Listing) -> dict:
        """Full Rightmove-style detail for the public listing page."""
        return {
            **listing_card(l),
            "photos": listing_gallery(l),
            "description": l.description or "",
            "amenities": l.amenities or [],
            "availableFrom": l.available_from or "",
            "depositGBP": l.deposit_gbp or 0,
        }

    @app.get("/agency/listings")
    def agency_listings():
        user, err = require_role("agency")
        if err:
            return err
        listings = SessionLocal.execute(
            select(Listing).where(Listing.agency_id == user.id).order_by(Listing.id.desc())
        ).scalars().all()
        return jsonify(
            {
                "kpis": {
                    "published": sum(1 for l in listings if l.status == "published"),
                    "moderation": sum(1 for l in listings if l.status == "moderation"),
                    "matches": sum(l.matches for l in listings),
                    "views": 142,
                },
                "listings": [listing_row(l) for l in listings],
            }
        )

    @app.post("/agency/listings")
    def agency_add_listing():
        user, err = require_role("agency")
        if err:
            return err
        d = request.get_json(silent=True) or {}
        try:
            l = Listing(
                agency_id=user.id,
                price_gbp=int(d.get("priceGBP") or 0),
                addr=(d.get("addr") or "").strip(),
                area=(d.get("area") or "").strip(),
                rooms=int(d.get("rooms") or 0),
                baths=int(d.get("baths") or 1),
                furnished=bool(d.get("furnished", True)),
                status="moderation",
                matches=0,
                description=(d.get("description") or "").strip()[:4000],
                amenities=_clean_amenities(d.get("amenities")),
                property_type=(d.get("propertyType") or "flat").strip()[:32],
                available_from=(d.get("availableFrom") or "").strip()[:32],
                deposit_gbp=int(d.get("depositGBP") or 0),
            )
        except (TypeError, ValueError):
            return jsonify({"error": "invalid"}), 400
        SessionLocal.add(l)
        SessionLocal.commit()
        return jsonify(listing_row(l)), 201

    def _apply_listing_fields(l: Listing, d: dict) -> None:
        """Update the editable listing fields present in `d` (shared by the
        operator and agency edit endpoints)."""
        if "priceGBP" in d:
            try:
                l.price_gbp = int(d.get("priceGBP") or 0)
            except (TypeError, ValueError):
                pass
        if "addr" in d:
            l.addr = (d.get("addr") or "").strip()[:255]
        if "area" in d:
            l.area = (d.get("area") or "").strip()[:64]
        if "rooms" in d:
            try:
                l.rooms = int(d.get("rooms") or 0)
            except (TypeError, ValueError):
                pass
        if "baths" in d:
            try:
                l.baths = int(d.get("baths") or 1)
            except (TypeError, ValueError):
                pass
        if "furnished" in d:
            l.furnished = bool(d.get("furnished"))
        if "description" in d:
            l.description = (d.get("description") or "").strip()[:4000]
        if "amenities" in d:
            l.amenities = _clean_amenities(d.get("amenities"))
        if "propertyType" in d:
            l.property_type = (d.get("propertyType") or "flat").strip()[:32]
        if "availableFrom" in d:
            l.available_from = (d.get("availableFrom") or "").strip()[:32]
        if "depositGBP" in d:
            try:
                l.deposit_gbp = int(d.get("depositGBP") or 0)
            except (TypeError, ValueError):
                pass
        if "photos" in d and isinstance(d.get("photos"), list):
            photos = [str(p).strip()[:512] for p in d["photos"] if str(p).strip()]
            l.photo_url = photos[0] if photos else None
            l.photos = photos[1:]

    def _own_listing(user: User, lid: int) -> Listing | None:
        l = SessionLocal.get(Listing, lid)
        return l if (l and l.agency_id == user.id) else None

    @app.patch("/agency/listings/<int:lid>")
    def agency_update_listing(lid: int):
        user, err = require_role("agency")
        if err:
            return err
        l = _own_listing(user, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        _apply_listing_fields(l, request.get_json(silent=True) or {})
        l.status = "moderation"  # an edit re-enters moderation
        SessionLocal.commit()
        return jsonify(listing_row(l))

    @app.delete("/agency/listings/<int:lid>")
    def agency_delete_listing(lid: int):
        user, err = require_role("agency")
        if err:
            return err
        l = _own_listing(user, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        SessionLocal.delete(l)
        SessionLocal.commit()
        return jsonify({"ok": True})

    @app.post("/agency/listings/<int:lid>/photo")
    def agency_listing_photo(lid: int):
        user, err = require_role("agency")
        if err:
            return err
        l = _own_listing(user, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_IMG:
            return jsonify({"error": "bad type", "code": "bad_type"}), 400
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        url = f"/api/uploads/{name}"
        if not l.photo_url:
            l.photo_url = url
        else:
            l.photos = [*(l.photos or []), url]
        SessionLocal.commit()
        return jsonify(listing_row(l))

    # ---- Agency listing moderation (operator) -----------------------------
    def agency_name_map() -> dict:
        return {
            u.id: u.name
            for u in SessionLocal.execute(select(User).where(User.role == "agency")).scalars().all()
        }

    def admin_listing_row(l: Listing, agencies: dict) -> dict:
        return {
            "id": l.id,
            "priceGBP": l.price_gbp,
            "addr": l.addr,
            "area": l.area,
            "rooms": l.rooms,
            "baths": l.baths,
            "furnished": l.furnished,
            "status": l.status,
            "photoUrl": l.photo_url,
            "photos": listing_gallery(l),
            "description": l.description or "",
            "amenities": l.amenities or [],
            "propertyType": l.property_type or "flat",
            "availableFrom": l.available_from or "",
            "depositGBP": l.deposit_gbp or 0,
            "agency": agencies.get(l.agency_id, ""),
            "createdAt": l.created_at.isoformat() if l.created_at else None,
        }

    @app.get("/admin/listings")
    def admin_listings():
        user, err = require_role("operator")
        if err:
            return err
        rows = SessionLocal.execute(select(Listing).order_by(Listing.id.desc())).scalars().all()
        ag = agency_name_map()
        return jsonify({"listings": [admin_listing_row(l, ag) for l in rows]})

    @app.post("/admin/listings/<int:lid>/status")
    def admin_listing_status(lid: int):
        user, err = require_role("operator")
        if err:
            return err
        l = SessionLocal.get(Listing, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        status = d.get("status")
        if status not in ("published", "moderation", "rejected"):
            return jsonify({"error": "bad status"}), 400
        l.status = status
        SessionLocal.commit()
        return jsonify(admin_listing_row(l, agency_name_map()))

    @app.patch("/admin/listings/<int:lid>")
    def admin_listing_update(lid: int):
        user, err = require_role("operator")
        if err:
            return err
        l = SessionLocal.get(Listing, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        d = request.get_json(silent=True) or {}
        if "priceGBP" in d:
            try:
                l.price_gbp = int(d.get("priceGBP") or 0)
            except (TypeError, ValueError):
                pass
        if "addr" in d:
            l.addr = (d.get("addr") or "").strip()[:255]
        if "area" in d:
            l.area = (d.get("area") or "").strip()[:64]
        if "rooms" in d:
            try:
                l.rooms = int(d.get("rooms") or 0)
            except (TypeError, ValueError):
                pass
        if "baths" in d:
            try:
                l.baths = int(d.get("baths") or 1)
            except (TypeError, ValueError):
                pass
        if "furnished" in d:
            l.furnished = bool(d.get("furnished"))
        if "description" in d:
            l.description = (d.get("description") or "").strip()[:4000]
        if "amenities" in d:
            l.amenities = _clean_amenities(d.get("amenities"))
        if "propertyType" in d:
            l.property_type = (d.get("propertyType") or "flat").strip()[:32]
        if "availableFrom" in d:
            l.available_from = (d.get("availableFrom") or "").strip()[:32]
        if "depositGBP" in d:
            try:
                l.deposit_gbp = int(d.get("depositGBP") or 0)
            except (TypeError, ValueError):
                pass
        if "photos" in d and isinstance(d.get("photos"), list):
            # Reorder/remove gallery photos; the first becomes the cover.
            photos = [str(p).strip()[:512] for p in d["photos"] if str(p).strip()]
            l.photo_url = photos[0] if photos else None
            l.photos = photos[1:]
        SessionLocal.commit()
        return jsonify(admin_listing_row(l, agency_name_map()))

    @app.post("/admin/listings/<int:lid>/photo")
    def admin_listing_photo(lid: int):
        user, err = require_role("operator")
        if err:
            return err
        l = SessionLocal.get(Listing, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "no file"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_IMG:
            return jsonify({"error": "bad type", "code": "bad_type"}), 400
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
        url = f"/api/uploads/{name}"
        # First upload becomes the cover; later uploads extend the gallery.
        if not l.photo_url:
            l.photo_url = url
        else:
            l.photos = [*(l.photos or []), url]
        SessionLocal.commit()
        return jsonify(admin_listing_row(l, agency_name_map()))

    @app.delete("/admin/listings/<int:lid>")
    def admin_listing_delete(lid: int):
        user, err = require_role("operator")
        if err:
            return err
        l = SessionLocal.get(Listing, lid)
        if not l:
            return jsonify({"error": "not found"}), 404
        SessionLocal.delete(l)
        SessionLocal.commit()
        return jsonify({"ok": True})

    # ---- Public housing catalog (no auth) ---------------------------------
    @app.get("/listings")
    def public_listings():
        rows = SessionLocal.execute(
            select(Listing).where(Listing.status == "published").order_by(Listing.id.desc())
        ).scalars().all()
        return jsonify({"listings": [listing_card(l) for l in rows]})

    @app.get("/listings/<int:lid>")
    def public_listing_detail(lid: int):
        l = SessionLocal.get(Listing, lid)
        if not l or l.status != "published":
            return jsonify({"error": "not found"}), 404
        return jsonify(listing_detail(l))

    @app.get("/og")
    def og_preview():
        """Public OpenGraph preview for a pasted listing URL (photo/title/price),
        so the housing search can show a rich card before the user signs in —
        same scrape the cabinet uses. Blocks obviously-internal hosts (SSRF)."""
        url = (request.args.get("url") or "").strip()
        low = url.lower()
        if not low.startswith(("http://", "https://")):
            return jsonify({})
        host = urllib.parse.urlparse(url).hostname or ""
        if host in ("localhost", "127.0.0.1", "::1") or host.startswith(
            ("10.", "192.168.", "127.", "169.254.")
        ) or host.endswith(".local"):
            return jsonify({})
        return jsonify(fetch_og_meta(url))

    # ---- Runner ------------------------------------------------------------
    # inProgress (set when arrival details are entered) advances into the field-visit
    # stages just like todo, so a runner can still progress an airport-meet.
    _NEXT_STAGE = {"todo": "onWay", "inProgress": "onWay", "onWay": "arrived", "arrived": "done"}

    def client_name_map() -> dict:
        return {c.id: c.name for c in SessionLocal.execute(select(Client)).scalars().all()}

    def runner_task_row(t: Task, names: dict) -> dict:
        return {
            "id": t.id,
            "time": t.time,
            "kind": t.kind,
            "key": t.key,
            "clientId": t.client_id,
            "client": names.get(t.client_id, ""),
            "addr": t.addr,
            "stage": t.status,
        }

    @app.get("/runner/tasks")
    def runner_tasks():
        user, err = require_role("runner")
        if err:
            return err
        # A runner's schedule = their timed field visits.
        tasks = SessionLocal.execute(
            select(Task).where(Task.runner_id == user.id, Task.time != "").order_by(Task.time, Task.position)
        ).scalars().all()
        names = client_name_map()
        return jsonify(
            {
                "name": user.name,
                "total": len(tasks),
                "done": sum(1 for t in tasks if t.status == "done"),
                "tasks": [runner_task_row(t, names) for t in tasks],
            }
        )

    @app.post("/runner/tasks/<int:task_id>/advance")
    def runner_advance(task_id: int):
        user, err = require_role("runner")
        if err:
            return err
        t = SessionLocal.get(Task, task_id)
        if not t or t.runner_id != user.id:
            return jsonify({"error": "not found"}), 404
        if t.status in _NEXT_STAGE:
            t.status = _NEXT_STAGE[t.status]
            if t.status == "done":
                t.completed_at = datetime.utcnow()
            SessionLocal.commit()
            if t.status == "done":
                notify_task_done(SessionLocal.get(Client, t.client_id), t)
        return jsonify(runner_task_row(t, client_name_map()))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
