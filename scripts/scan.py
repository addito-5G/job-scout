#!/usr/bin/env python3
"""Сканирование вакансий из настроенных источников."""

from __future__ import annotations

import argparse

from cli_logging import setup_cli_logging
from db import get_session, init_db
from services.scan_service import run_scan

logger = setup_cli_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — scan vacancies")
    parser.add_argument("--url", help="Добавить вакансию по URL вручную")
    parser.add_argument("--title", default="", help="Заголовок для --url")
    parser.add_argument("--company", default="", help="Компания для --url")
    parser.add_argument("--match-limit", type=int, default=50, help="Лимит fit-матчинга после скана")
    parser.add_argument("--no-match", action="store_true", help="Только парсинг, без расчёта соответствия")
    args = parser.parse_args()

    init_db()
    session = get_session()
    result = run_scan(
        session,
        manual_url=args.url,
        manual_title=args.title,
        manual_company=args.company,
        run_match=not args.no_match,
        match_limit=args.match_limit,
    )
    session.close()

    print(
        f"\nГотово: собрано {result.scraped}, в БД {result.saved} "
        f"(новых {result.new_count}, обновлено {result.updated_count})"
    )
    if not args.no_match:
        print(f"Fit score: {result.matched_count} вакансий")
    if result.by_source:
        print("По источникам:", ", ".join(f"{k}={v}" for k, v in result.by_source.items()))
    if result.errors:
        print("Ошибки:")
        for err in result.errors[:5]:
            print(f"  - {err}")
    print("UI:       streamlit run app.py")


if __name__ == "__main__":
    main()
