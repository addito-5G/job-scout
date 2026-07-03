#!/usr/bin/env python3
"""Инициализация таблиц SQLAlchemy в SQLite (Alembic)."""

from __future__ import annotations

from sqlalchemy import inspect

from db import get_engine, init_db
from db.tables import Base


def main() -> None:
    init_db()
    engine = get_engine()
    existing = set(inspect(engine).get_table_names())
    tables = sorted(name for name in Base.metadata.tables if name in existing)
    print("✅ Database schema ready (alembic head):")
    for name in tables:
        print(f"  - {name}")
    print(f"\nDB: {engine.url}")


if __name__ == "__main__":
    main()
