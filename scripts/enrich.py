#!/usr/bin/env python3
"""Обогащение вакансий полным описанием через браузер."""

from __future__ import annotations

import argparse


from cli_logging import setup_cli_logging
from config_loader import load_criteria_with_browser
from db import init_db
from enricher import enrich_vacancies

logger = setup_cli_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — enrich vacancies")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-score", type=int, default=None)
    args = parser.parse_args()

    criteria = load_criteria_with_browser()
    browser = criteria.get("browser", {})

    limit = args.limit if args.limit is not None else int(browser.get("enrich_limit", 30))
    min_score = args.min_score if args.min_score is not None else int(
        criteria.get("thresholds", {}).get("min_score", 0)
    )
    delay = float(browser.get("delay_seconds", 2))

    init_db()

    print(f"→ Обогащение до {limit} вакансий (score≥{min_score})...")
    enriched, errors = enrich_vacancies(
        criteria=criteria,
        limit=limit,
        min_score=min_score,
        delay_seconds=delay,
    )
    print(f"\nГотово: обогащено {enriched}, ошибок {len(errors)}")
    if errors:
        print("Первые ошибки:")
        for err in errors[:5]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
