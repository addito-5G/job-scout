"""Подключение к БД и фабрика сессий."""

from __future__ import annotations

import config
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from db.tables import Vacancy

_engine = None
_SessionLocal = None
_schema_initialized = False


def resolve_database_url(url: str) -> str:
    if url.startswith("sqlite:///./"):
        path = config.ROOT / url.removeprefix("sqlite:///./")
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"
    return url


def get_engine():
    global _engine
    if _engine is None:
        url = resolve_database_url(config.DATABASE_URL)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)

        if url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def get_session():
    return get_session_factory()()


def init_db() -> None:
    global _schema_initialized
    engine = get_engine()
    if not _schema_initialized:
        from db.migrations import apply_migrations

        apply_migrations(engine)
        _schema_initialized = True

    from services.profile_filter_service import backfill_profile_roles

    session = get_session()
    try:
        null_roles = session.execute(
            select(func.count()).select_from(Vacancy).where(Vacancy.profile_role.is_(None))
        ).scalar_one()
        if null_roles:
            backfill_profile_roles(session)
    finally:
        session.close()
