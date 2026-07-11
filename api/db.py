from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, future=True))
Base = declarative_base()


def init_db():
    import models  # noqa: F401 — register models on Base

    Base.metadata.create_all(bind=engine)
