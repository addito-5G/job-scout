"""Миграция схемы под изолированные профили резюме."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


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
    _ensure_vacancy_profile_scoped_uniques(engine)


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


def _vacancies_create_sql(conn) -> str | None:
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='vacancies'")
    ).fetchone()
    return row[0] if row else None


def _has_legacy_global_vacancy_uniques(conn) -> bool:
    """True if vacancies still has UNIQUE(external_url) or UNIQUE(source, external_id)."""
    create_sql = _vacancies_create_sql(conn) or ""
    compact = create_sql.replace(" ", "").lower()
    if "unique(external_url)" in compact:
        return True
    # Table-level UNIQUE(source, external_id) without profile_id (legacy).
    if "constraintuq_vacancy_source_externalunique(source,external_id)" in compact:
        return True
    if "unique(source,external_id)" in compact and "unique(profile_id,source,external_id)" not in compact:
        # May be only the named constraint; profile unique is usually an INDEX not in CREATE.
        if "uq_vacancy_source_external" in create_sql:
            return True
    return False


def _ensure_vacancy_profile_scoped_uniques(engine: Engine) -> None:
    """Rebuild vacancies without global UNIQUE(url)/(source,id) — identity is per profile."""
    if engine.dialect.name != "sqlite":
        return

    with engine.connect() as conn:
        if "vacancies" not in {
            r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }:
            return
        needs_rebuild = _has_legacy_global_vacancy_uniques(conn)

    if needs_rebuild:
        _rebuild_vacancies_drop_global_uniques(engine)

    with engine.begin() as conn:
        indexes = {row[1] for row in conn.execute(text("PRAGMA index_list(vacancies)"))}
        if "uq_vacancy_source_external" in indexes:
            conn.execute(text("DROP INDEX IF EXISTS uq_vacancy_source_external"))
        if "uq_vacancy_profile_source_external" not in indexes:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancy_profile_source_external "
                    "ON vacancies(profile_id, source, external_id)"
                )
            )


def _rebuild_vacancies_drop_global_uniques(engine: Engine) -> None:
    """SQLite cannot DROP table UNIQUE columns — recreate vacancies without them."""
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(vacancies)")).fetchall()]
        if not cols:
            return
        default_id = _default_profile_id(conn)
        conn.execute(
            text("UPDATE vacancies SET profile_id = :pid WHERE profile_id IS NULL"),
            {"pid": default_id},
        )

        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text("DROP TABLE IF EXISTS vacancies__rebuild"))
        conn.execute(
            text(
                """
                CREATE TABLE vacancies__rebuild (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    source VARCHAR(32) NOT NULL,
                    external_id VARCHAR(128) NOT NULL,
                    external_url VARCHAR(1024) NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    title_normalized VARCHAR(512),
                    company_id INTEGER,
                    department VARCHAR(255),
                    description_short TEXT,
                    description_full TEXT,
                    description_raw TEXT,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    salary_currency VARCHAR(16) NOT NULL DEFAULT 'RUR',
                    salary_gross BOOLEAN NOT NULL DEFAULT 0,
                    salary_text VARCHAR(255),
                    work_format VARCHAR(32),
                    work_format_raw VARCHAR(128),
                    schedule VARCHAR(64),
                    employment VARCHAR(128),
                    location_id INTEGER,
                    location_text VARCHAR(255),
                    address VARCHAR(512),
                    experience_required VARCHAR(64),
                    experience_years_min INTEGER,
                    experience_years_max INTEGER,
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    user_status VARCHAR(32) NOT NULL DEFAULT 'new',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    published_at DATETIME,
                    updated_at_source DATETIME,
                    scraped_at DATETIME NOT NULL,
                    enriched_at DATETIME,
                    raw_data TEXT,
                    search_settings_id INTEGER,
                    profile_role VARCHAR(64),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY(company_id) REFERENCES companies (id),
                    FOREIGN KEY(location_id) REFERENCES locations (id),
                    FOREIGN KEY(profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE,
                    FOREIGN KEY(search_settings_id) REFERENCES search_settings (id)
                )
                """
            )
        )

        # Insert intersecting columns only (ignore dropped legacy cols like rule_score).
        rebuild_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(vacancies__rebuild)")).fetchall()
        }
        shared = [c for c in cols if c in rebuild_cols]
        shared_sql = ", ".join(shared)
        conn.execute(
            text(
                f"INSERT INTO vacancies__rebuild ({shared_sql}) "
                f"SELECT {shared_sql} FROM vacancies"
            )
        )
        conn.execute(text("DROP TABLE vacancies"))
        conn.execute(text("ALTER TABLE vacancies__rebuild RENAME TO vacancies"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancy_profile_source_external "
                "ON vacancies(profile_id, source, external_id)"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vacancies_profile ON vacancies(profile_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vacancies_published ON vacancies(published_at)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_vacancies_salary ON vacancies(salary_from, salary_to)")
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vacancies_format ON vacancies(work_format)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_vacancies_status ON vacancies(status, is_active)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_vacancies_profile_role ON vacancies(profile_role)")
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_vacancies_external_url ON vacancies(external_url)"))
        conn.execute(text("PRAGMA foreign_keys=ON"))

