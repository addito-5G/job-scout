"""Нормализация полей vacancies (source, work_format) для legacy SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import config
from db.engine import resolve_database_url
from db.normalize import normalize_source, normalize_work_format


def sqlite_database_path() -> Path:
    url = resolve_database_url(config.DATABASE_URL)
    return Path(url.removeprefix("sqlite:///"))


def migrate_vacancy_rows(conn: sqlite3.Connection) -> dict[str, int]:
    """Нормализовать source/work_format; uniqueness is per (profile_id, source, external_id)."""
    stats = {"rows": 0, "normalized_sources": 0, "work_format_filled": 0}

    if "vacancies" not in {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }:
        return stats

    cols = {row[1] for row in conn.execute("PRAGMA table_info(vacancies)")}
    if "work_format" not in cols:
        conn.execute("ALTER TABLE vacancies ADD COLUMN work_format TEXT")
    if "work_schedule" not in cols:
        conn.execute("ALTER TABLE vacancies ADD COLUMN work_schedule TEXT")

    rows = conn.execute("SELECT * FROM vacancies").fetchall()
    col_names = [d[1] for d in conn.execute("PRAGMA table_info(vacancies)").fetchall()]
    stats["rows"] = len(rows)

    for row in rows:
        data = dict(zip(col_names, row))
        old_source = data["source"]
        new_source = normalize_source(old_source)
        location = data.get("location_text") or data.get("location")
        work_format = normalize_work_format(data.get("work_schedule"), location)

        conn.execute(
            """
            UPDATE vacancies SET
                source = ?,
                work_format = COALESCE(work_format, ?)
            WHERE id = ?
            """,
            (new_source, work_format, data["id"]),
        )
        if old_source != new_source:
            stats["normalized_sources"] += 1
        if work_format:
            stats["work_format_filled"] += 1

    conn.commit()

    indexes = {row[1] for row in conn.execute("PRAGMA index_list(vacancies)").fetchall()}
    cols = {row[1] for row in conn.execute("PRAGMA table_info(vacancies)")}
    if "profile_id" in cols and "uq_vacancy_profile_source_external" not in indexes:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancy_profile_source_external
            ON vacancies(profile_id, source, external_id)
            """
        )
        conn.commit()

    return stats


def run_vacancy_data_migration(db_path: Path | None = None) -> dict[str, int]:
    """Подключиться к SQLite и выполнить нормализацию vacancies."""
    path = db_path or sqlite_database_path()
    conn = sqlite3.connect(path)
    try:
        return migrate_vacancy_rows(conn)
    finally:
        conn.close()
