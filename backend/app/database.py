from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _database_connect_args(database_url: str) -> dict:
    parsed = urlparse(database_url)
    host = parsed.hostname or ""

    if parsed.scheme.startswith("sqlite"):
        return {}

    if host in {"localhost", "127.0.0.1", "db"}:
        return {}

    if "sslmode=" in database_url:
        return {}

    return {"sslmode": "require"}


engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=_database_connect_args(settings.DATABASE_URL),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
