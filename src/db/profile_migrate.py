"""Миграция схемы под изолированные профили резюме."""

from __future__ import annotations

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine

from db.tables import Base, CandidateProfile, Vacancy


def ensure_profile_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "candidate_profiles" not in tables:
        return

    with engine.begin() as conn:
        profile_cols = {c["name"] for c in inspector.get_columns("candidate_profiles")}
        if "display_name" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN display_name VARCHAR(255)"))
            conn.execute(
                text(
                    "UPDATE candidate_profiles SET display_name = COALESCE(title, full_name, 'Профиль #' || id)"
                )
            )

        company_cols = {c["name"] for c in inspector.get_columns("companies")} if "companies" in tables else set()
        if company_cols and "ai_brief" not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN ai_brief VARCHAR(200)"))

        if "search_settings" in tables:
            ss_cols = {c["name"] for c in inspector.get_columns("search_settings")}
            if "sources_enabled_json" not in ss_cols:
                conn.execute(text("ALTER TABLE search_settings ADD COLUMN sources_enabled_json TEXT"))

        if "daily_metrics" in tables:
            dm_cols = {c["name"] for c in inspector.get_columns("daily_metrics")}
            if "profile_id" not in dm_cols:
                conn.execute(text("ALTER TABLE daily_metrics ADD COLUMN profile_id INTEGER"))

    _backfill_vacancy_profile_ids(engine)


def _default_profile_id(conn) -> int:
    row = conn.execute(
        text("SELECT id FROM candidate_profiles ORDER BY is_active DESC, updated_at DESC LIMIT 1")
    ).fetchone()
    if row:
        return int(row[0])
    conn.execute(
        text(
            "INSERT INTO candidate_profiles (display_name, is_active, salary_currency, created_at, updated_at) "
            "VALUES ('По умолчанию', 1, 'RUR', datetime('now'), datetime('now'))"
        )
    )
    return int(conn.execute(text("SELECT last_insert_rowid()")).scalar_one())


def _backfill_vacancy_profile_ids(engine: Engine) -> None:
    inspector = inspect(engine)
    if "vacancies" not in inspector.get_table_names():
        return
    vac_cols = {c["name"] for c in inspector.get_columns("vacancies")}
    if "profile_id" not in vac_cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE vacancies ADD COLUMN profile_id INTEGER"))
            default_id = _default_profile_id(conn)
            conn.execute(text("UPDATE vacancies SET profile_id = :pid WHERE profile_id IS NULL"), {"pid": default_id})

    with engine.connect() as conn:
        indexes = {row[1] for row in conn.execute(text("PRAGMA index_list(vacancies)"))}
    if "uq_vacancy_profile_source_external" not in indexes:
        with engine.begin() as conn:
            default_id = _default_profile_id(conn)
            conn.execute(text("UPDATE vacancies SET profile_id = :pid WHERE profile_id IS NULL"), {"pid": default_id})
            if "uq_vacancy_source_external" in indexes:
                conn.execute(text("DROP INDEX IF EXISTS uq_vacancy_source_external"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancy_profile_source_external "
                    "ON vacancies(profile_id, source, external_id)"
                )
            )
