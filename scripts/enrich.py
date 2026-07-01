#!/usr/bin/env python3
"""Обогащение вакансий полным описанием через браузер."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from db import init_db
from enricher import enrich_vacancies

logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — enrich vacancies")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-score", type=int, default=None)
    args = parser.parse_args()

    criteria = load_yaml(ROOT / "config" / "criteria.yaml")
    raw_sources = load_yaml(ROOT / "config" / "sources.yaml")
    browser = raw_sources.get("browser", {})

    limit = args.limit if args.limit is not None else int(browser.get("enrich_limit", 30))
    min_score = args.min_score if args.min_score is not None else int(
        criteria.get("thresholds", {}).get("min_score", 0)
    )
    delay = float(browser.get("delay_seconds", 2))

    criteria["browser"] = browser
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
