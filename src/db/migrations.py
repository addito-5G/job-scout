"""Применение миграций Alembic."""

from __future__ import annotations

import os
from pathlib import Path

import config
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def alembic_config() -> Config:
    ini_path = config.ROOT / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(config.ROOT / "alembic"))
    cfg.set_main_option("prepend_sys_path", f".{os.pathsep}src")
    return cfg


def apply_migrations(engine: Engine) -> None:
    """Прогон миграций: upgrade head или stamp для legacy БД без alembic_version."""
    from db.schema_migrate import ensure_schema

    ensure_schema(engine)

    from db.profile_migrate import ensure_profile_schema

    ensure_profile_schema(engine)

    inspector = inspect(engine)
    has_app_tables = "vacancies" in inspector.get_table_names()

    with engine.connect() as conn:
        current = MigrationContext.configure(conn).get_current_revision()

    cfg = alembic_config()

    if has_app_tables and current is None:
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")
