from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, future=True))
Base = declarative_base()

# Additive column migrations for columns added to ALREADY-EXISTING tables.
# create_all() creates new tables/columns for new tables, but never alters an
# existing table, so new columns on old tables are added here (Postgres
# ADD COLUMN IF NOT EXISTS — idempotent, safe to run on every boot).
_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS track_token VARCHAR(48)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_track_token ON users (track_token)",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS mode VARCHAR(12) DEFAULT 'car'",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS origin_lat DOUBLE PRECISION",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS origin_lng DOUBLE PRECISION",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS route_at TIMESTAMP",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_lat DOUBLE PRECISION",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_lng DOUBLE PRECISION",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_loc_at TIMESTAMP",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS legs_json JSON",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS phase VARCHAR(16) DEFAULT 'toPickup'",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS pickup_label VARCHAR(255)",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS pickup_lat DOUBLE PRECISION",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS pickup_lng DOUBLE PRECISION",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS at_pickup BOOLEAN DEFAULT FALSE",
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS client_read_manager_at TIMESTAMP",
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS staff_read_manager_at TIMESTAMP",
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS client_read_runner_at TIMESTAMP",
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS staff_read_runner_at TIMESTAMP",
]


def init_db():
    import models  # noqa: F401 — register models on Base

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))
