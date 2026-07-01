#!/usr/bin/env python3
"""Миграция таблицы vacancies: нормализация source, work_format, UNIQUE(source, external_id)."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import config
from db.normalize import normalize_source, normalize_work_format, parse_datetime
from db.models import resolve_database_url


def _db_path() -> Path:
    url = resolve_database_url(config.DATABASE_URL)
    return Path(url.replace("sqlite:///", ""))


def migrate(conn: sqlite3.Connection) -> dict:
    stats = {"rows": 0, "normalized_sources": 0, "work_format_filled": 0}

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
        work_format = normalize_work_format(data.get("work_schedule"), data.get("location"))

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

    # UNIQUE(source, external_id)
    indexes = {
        row[1] for row in conn.execute("PRAGMA index_list(vacancies)").fetchall()
    }
    if "uq_vacancy_source_external" not in indexes:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancy_source_external
            ON vacancies(source, external_id)
            """
        )
        conn.commit()

    return stats


def main() -> None:
    path = _db_path()
    print(f"📦 Migrating: {path}")
    conn = sqlite3.connect(path)
    try:
        stats = migrate(conn)
        total = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]
        by_source = conn.execute(
            "SELECT source, COUNT(*) FROM vacancies GROUP BY source"
        ).fetchall()
        print(f"✅ Rows: {stats['rows']}, normalized sources: {stats['normalized_sources']}")
        print(f"   work_format filled: {stats['work_format_filled']}")
        print(f"   Total in DB: {total}")
        for src, cnt in by_source:
            print(f"   - {src}: {cnt}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
