#!/usr/bin/env python3
"""Миграция таблицы vacancies: нормализация source, work_format, UNIQUE(source, external_id)."""

from __future__ import annotations

import sqlite3

from db.vacancy_data_migrate import run_vacancy_data_migration, sqlite_database_path


def main() -> None:
    path = sqlite_database_path()
    print(f"📦 Migrating: {path}")
    stats = run_vacancy_data_migration(path)

    conn = sqlite3.connect(path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]
        by_source = conn.execute("SELECT source, COUNT(*) FROM vacancies GROUP BY source").fetchall()
    finally:
        conn.close()

    print(f"✅ Rows: {stats['rows']}, normalized sources: {stats['normalized_sources']}")
    print(f"   work_format filled: {stats['work_format_filled']}")
    print(f"   Total in DB: {total}")
    for src, cnt in by_source:
        print(f"   - {src}: {cnt}")


if __name__ == "__main__":
    main()
