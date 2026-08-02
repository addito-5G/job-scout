"""Миграция vacancies: снятие глобальных UNIQUE(url)/(source,id)."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from db.profile_migrate import ensure_profile_schema, _has_legacy_global_vacancy_uniques


def test_rebuild_drops_global_url_unique(tmp_path):
    db = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE candidate_profiles (
                    id INTEGER PRIMARY KEY,
                    display_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT 1,
                    salary_currency VARCHAR(16) DEFAULT 'RUR',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO candidate_profiles (id, display_name, is_active, created_at, updated_at)
                VALUES (1, 'P1', 1, datetime('now'), datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE vacancies (
                    id INTEGER PRIMARY KEY,
                    profile_id INTEGER,
                    source VARCHAR(32) NOT NULL,
                    external_id VARCHAR(128) NOT NULL,
                    external_url VARCHAR(1024) NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    salary_currency VARCHAR(16) NOT NULL DEFAULT 'RUR',
                    salary_gross BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    user_status VARCHAR(32) NOT NULL DEFAULT 'new',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    scraped_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    CONSTRAINT uq_vacancy_source_external UNIQUE (source, external_id),
                    UNIQUE (external_url)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO vacancies (
                    id, profile_id, source, external_id, external_url, title,
                    scraped_at, created_at, updated_at
                ) VALUES (
                    1, 1, 'hh', '111', 'https://hh.ru/vacancy/111', 'PM',
                    datetime('now'), datetime('now'), datetime('now')
                )
                """
            )
        )

    with engine.connect() as conn:
        assert _has_legacy_global_vacancy_uniques(conn) is True

    ensure_profile_schema(engine)

    with engine.connect() as conn:
        assert _has_legacy_global_vacancy_uniques(conn) is False
        # Same URL under second profile must be allowed after rebuild.
        conn.execute(
            text(
                """
                INSERT INTO candidate_profiles (id, display_name, is_active, created_at, updated_at)
                VALUES (2, 'P2', 1, datetime('now'), datetime('now'))
                """
            )
        )
        conn.commit()
        conn.execute(
            text(
                """
                INSERT INTO vacancies (
                    profile_id, source, external_id, external_url, title,
                    scraped_at, created_at, updated_at
                ) VALUES (
                    2, 'hh', '111', 'https://hh.ru/vacancy/111', 'PM copy',
                    datetime('now'), datetime('now'), datetime('now')
                )
                """
            )
        )
        conn.commit()
        n = conn.execute(text("SELECT COUNT(*) FROM vacancies WHERE external_url LIKE '%111%'")).scalar()
        assert n == 2
