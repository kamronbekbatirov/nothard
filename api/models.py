from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from catalog import PACKAGE_AMOUNT  # re-exported for callers that import it here


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # client | operator | agency | runner | admin
    role: Mapped[str] = mapped_column(String(32), default="client")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    telegram_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # One-time code for linking Telegram from the cabinet via the bot deep-link.
    tg_link_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Set once the user accepts the Privacy Policy + Terms after first sign-in.
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Email verification / passwordless login codes.
    pending_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    email_code_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Chosen interface language — persisted so Telegram messages go in it.
    locale: Mapped[str] = mapped_column(String(8), default="ru")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_public(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "telegram_id": self.telegram_id,
            "telegram_username": self.telegram_username,
            "photo_url": self.photo_url,
            "termsAccepted": bool(self.terms_accepted_at),
            "locale": self.locale or "ru",
        }


class Session(Base):
    """A signed-in device/session for a user. The access token carries this row's
    id (``sid``); revoking the row (revoked=True) invalidates that token on the
    next request. One row per device: re-login from the same device reuses it
    (keyed by device_id) instead of piling up duplicate sessions."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Stable per-browser identifier the client stores locally (survives logout),
    # so a logout→login on the same device maps back to this same session.
    device_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    ip: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(String(512), default="")
    browser: Mapped[str] = mapped_column(String(64), default="")
    os: Mapped[str] = mapped_column(String(64), default="")
    device: Mapped[str] = mapped_column(String(32), default="")  # Desktop|Mobile|Tablet
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Client(Base):
    """A relocation customer profile. Tied to a login account (user_id) when the
    customer registered; may be null for records created only by the operator."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    # Manager is assigned by an operator — no auto-assignment.
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    runner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    documents: Mapped[dict] = mapped_column(JSON, default=dict)
    # Opaque token for a public, read-only "share your relocation with family" page.
    share_token: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Order(Base):
    """A single purchase — a package or an individual service."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    item_type: Mapped[str] = mapped_column(String(16), default="service")  # package|service
    item_id: Mapped[str] = mapped_column(String(64), default="")  # meet/housing/premium or service id
    amount_gbp: Mapped[int] = mapped_column(Integer, default=0)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="new")  # new|active|done
    # A completed package is archived once the client has reviewed/dismissed it,
    # so it stops showing as the active relocation and they can buy a new one.
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # collected intake fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Task(Base):
    """A work item derived from an order — one row per relocation step (package)
    or per purchased service. This is the client's 'path' and the runner's queue."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(16), default="step")  # step|service
    key: Mapped[str] = mapped_column(String(64), default="")  # step key or service id
    status: Mapped[str] = mapped_column(String(16), default="todo")  # todo|onWay|arrived|done
    runner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    time: Mapped[str] = mapped_column(String(16), default="")
    addr: Mapped[str] = mapped_column(String(255), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # When this step/service was marked done — kept as completion history for the
    # operator's finished-clients view. Cleared if the task is reopened.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Message(Base):
    """A chat message in one of a client's two threads: with their manager or
    with their field companion (runner)."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    sender: Mapped[str] = mapped_column(String(16), default="client")  # client | manager | runner
    # Which conversation this belongs to — the manager thread or the runner thread.
    channel: Mapped[str] = mapped_column(String(16), default="manager")  # manager | runner
    author_name: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Review(Base):
    """A client's rating + optional text left after completing a package."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    item_type: Mapped[str] = mapped_column(String(16), default="package")  # package|service
    package_id: Mapped[str] = mapped_column(String(64), default="")  # package or service id
    stars: Mapped[int] = mapped_column(Integer, default=5)
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HousingItem(Base):
    """An apartment a client is considering during housing search — either picked
    from our catalog or a link the client pasted. The operator tracks a status,
    schedules a viewing time, and uploads photos/videos after viewing it."""

    __tablename__ = "housing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    source: Mapped[str] = mapped_column(String(16), default="link")  # catalog|link
    ref: Mapped[str] = mapped_column(String(512), default="")  # property id or URL
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(String(512), default="")
    price_gbp: Mapped[int] = mapped_column(Integer, default=0)
    addr: Mapped[str] = mapped_column(String(255), default="")
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # new|viewing|viewed|secured|busy|declined
    status: Mapped[str] = mapped_column(String(16), default="new")
    viewing_at: Mapped[str] = mapped_column(String(64), default="")  # scheduled viewing time
    note: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HousingMedia(Base):
    """A photo/video the operator captured while viewing an apartment."""

    __tablename__ = "housing_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    housing_id: Mapped[int] = mapped_column(ForeignKey("housing_items.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    url: Mapped[str] = mapped_column(String(512), default="")
    filename: Mapped[str] = mapped_column(String(255), default="")
    kind: Mapped[str] = mapped_column(String(8), default="image")  # image|video
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Attachment(Base):
    """A file the operator uploaded — for a service order or a document step task."""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    filename: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price_gbp: Mapped[int] = mapped_column(Integer, default=0)
    addr: Mapped[str] = mapped_column(String(255), default="")
    area: Mapped[str] = mapped_column(String(64), default="")
    rooms: Mapped[int] = mapped_column(Integer, default=0)  # 0 = studio
    baths: Mapped[int] = mapped_column(Integer, default=1)
    furnished: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(16), default="moderation")  # published|moderation|rejected
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)  # cover photo
    matches: Mapped[int] = mapped_column(Integer, default=0)
    # Rich detail (Rightmove-style listing page).
    description: Mapped[str] = mapped_column(Text, default="")
    photos: Mapped[list] = mapped_column(JSON, default=list)  # extra photo URLs (gallery)
    amenities: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["wifi","washer"]
    property_type: Mapped[str] = mapped_column(String(32), default="flat")  # flat|studio|house|room
    available_from: Mapped[str] = mapped_column(String(32), default="")
    deposit_gbp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
