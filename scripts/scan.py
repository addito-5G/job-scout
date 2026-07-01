#!/usr/bin/env python3
"""Сканирование вакансий из настроенных источников."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from db import get_session, init_db
from services.scan_service import run_scan

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — scan vacancies")
    parser.add_argument("--url", help="Добавить вакансию по URL вручную")
    parser.add_argument("--title", default="", help="Заголовок для --url")
    parser.add_argument("--company", default="", help="Компания для --url")
    parser.add_argument("--min-display", type=int, default=None, help="Показывать в консоли только score≥N")
    args = parser.parse_args()

    init_db()
    session = get_session()
    result = run_scan(
        session,
        manual_url=args.url,
        manual_title=args.title,
        manual_company=args.company,
        display_min=args.min_display,
    )
    session.close()

    print(
        f"\nГотово: собрано {result.scraped}, в БД {result.saved} "
        f"(новых {result.new_count}, обновлено {result.updated_count}), "
        f"приоритет ★ {result.priority_count}"
    )
    if result.by_source:
        print("По источникам:", ", ".join(f"{k}={v}" for k, v in result.by_source.items()))
    if result.errors:
        print("Ошибки:")
        for err in result.errors[:5]:
            print(f"  - {err}")
    print("Матчинг:  python scripts/match.py")
    print("UI:       streamlit run app.py")


if __name__ == "__main__":
    main()
