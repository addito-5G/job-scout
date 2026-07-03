"""Тесты нормализации legacy-полей vacancies."""

from __future__ import annotations

import sqlite3

from db.vacancy_data_migrate import migrate_vacancy_rows


def _create_vacancies_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE vacancies (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            work_format TEXT,
            work_schedule TEXT,
            location_text TEXT
        )
        """
    )


def test_migrate_normalizes_source_and_work_format(tmp_path):
    db = tmp_path / "vacancies.db"
    conn = sqlite3.connect(db)
    _create_vacancies_table(conn)
    conn.execute(
        "INSERT INTO vacancies (source, external_id, work_schedule, location_text) VALUES (?, ?, ?, ?)",
        ("hh_parser", "123", "remote", "Москва"),
    )
    conn.commit()

    stats = migrate_vacancy_rows(conn)

    row = conn.execute("SELECT source, work_format FROM vacancies WHERE id = 1").fetchone()
    conn.close()

    assert stats["rows"] == 1
    assert stats["normalized_sources"] == 1
    assert stats["work_format_filled"] == 1
    assert row == ("hh", "remote")


def test_migrate_noop_when_table_missing(tmp_path):
    conn = sqlite3.connect(tmp_path / "empty.db")
    stats = migrate_vacancy_rows(conn)
    conn.close()
    assert stats == {"rows": 0, "normalized_sources": 0, "work_format_filled": 0}
