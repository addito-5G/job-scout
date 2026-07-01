#!/usr/bin/env python3
"""Инициализация таблиц SQLAlchemy в SQLite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from db import init_db, get_engine
from db.models import Base


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    tables = sorted(Base.metadata.tables.keys())
    print("✅ SQLAlchemy tables ready:")
    for name in tables:
        print(f"  - {name}")
    print(f"\nDB: {engine.url}")


if __name__ == "__main__":
    main()
