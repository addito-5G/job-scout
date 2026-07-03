"""Лёгкие миграции схемы без Alembic (legacy; новые изменения — через alembic/versions/)."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if "vacancies" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("vacancies")}
        if "search_settings_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE vacancies ADD COLUMN search_settings_id INTEGER"))
        if "profile_role" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE vacancies ADD COLUMN profile_role VARCHAR(64)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vacancies_profile_role ON vacancies (profile_role)"))
    if "search_settings" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("search_settings")}
        if "profile_label" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE search_settings ADD COLUMN profile_label VARCHAR(255)"))
