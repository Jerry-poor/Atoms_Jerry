from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args: dict | None = None
if settings.database_url.startswith("sqlite"):
    # Increase lock timeout and enable WAL for concurrent reads/writes (useful for dev/test SQLite).
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args or {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
