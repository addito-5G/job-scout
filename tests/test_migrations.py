"""Тесты Alembic-миграций."""

from __future__ import annotations

import config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from db.engine import get_engine, init_db
from db.migrations import alembic_config, apply_migrations
from db.tables import Base
from sqlalchemy import inspect


def _reset_engine() -> None:
    import db.engine as engine_module

    engine_module._engine = None
    engine_module._SessionLocal = None


def test_apply_migrations_creates_schema(monkeypatch, tmp_path):
    db_file = tmp_path / "fresh.db"
    monkeypatch.setattr(config, "DATABASE_URL", f"sqlite:///{db_file}")
    _reset_engine()

    apply_migrations(get_engine())

    inspector = inspect(get_engine())
    assert "vacancies" in inspector.get_table_names()
    assert "alembic_version" in inspector.get_table_names()

    with get_engine().connect() as conn:
        revision = MigrationContext.configure(conn).get_current_revision()
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    assert revision == head


def test_legacy_db_gets_stamped(monkeypatch, tmp_path):
    db_file = tmp_path / "legacy.db"
    monkeypatch.setattr(config, "DATABASE_URL", f"sqlite:///{db_file}")
    _reset_engine()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "vacancies" in inspector.get_table_names()
    assert "alembic_version" not in inspector.get_table_names()

    apply_migrations(engine)

    with engine.connect() as conn:
        revision = MigrationContext.configure(conn).get_current_revision()
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    assert revision == head


def test_init_db_runs_migrations_only_once(monkeypatch, tmp_path):
    db_file = tmp_path / "once.db"
    monkeypatch.setattr(config, "DATABASE_URL", f"sqlite:///{db_file}")

    import db.engine as engine_module
    from db.tables import Base

    calls: list[int] = []

    def _track(engine):
        calls.append(1)
        Base.metadata.create_all(engine)

    monkeypatch.setattr("db.migrations.apply_migrations", _track)
    engine_module._engine = None
    engine_module._SessionLocal = None
    engine_module._schema_initialized = False

    init_db()
    init_db()

    assert len(calls) == 1
