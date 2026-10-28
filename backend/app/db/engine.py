"""SQLAlchemy engine helpers for local SQLite."""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def normalize_database_url(url: str) -> str:
    """Map async SQLite URLs onto the sync driver used by this app."""
    if url.startswith("sqlite+aiosqlite:"):
        return "sqlite:" + url.removeprefix("sqlite+aiosqlite:")
    return url


def uses_sqlite(url: str) -> bool:
    if not url or url == "memory":
        return False
    return normalize_database_url(url).startswith("sqlite:")


def make_engine(url: str) -> Engine:
    normalized = normalize_database_url(url)
    connect_args: dict = {}
    engine_kwargs: dict = {"future": True}
    if normalized.startswith("sqlite:"):
        connect_args["check_same_thread"] = False
        if normalized in {"sqlite://", "sqlite:///:memory:"}:
            engine_kwargs["poolclass"] = StaticPool
    engine = create_engine(normalized, connect_args=connect_args, **engine_kwargs)

    if normalized.startswith("sqlite:"):

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
