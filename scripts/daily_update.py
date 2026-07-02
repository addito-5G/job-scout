#!/usr/bin/env python3
"""Ежедневное обновление: scan → match → analytics (для cron / launchd)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from analytics import build_analytics, snapshot_for_today
from db import get_session, init_db
from db.repositories.metrics_repo import save_daily_metrics
from enricher import enrich_vacancies
from services.scheduled_job import run_scheduled_update
from services.schedule_service import load_schedule

logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — daily update")
    parser.add_argument("--skip-scan", action="store_true", help="Пропустить scan+match")
    parser.add_argument("--skip-enrich", action="store_true")
    parser.add_argument("--trigger", default="scheduled", choices=["scheduled", "manual"])
    args = parser.parse_args()

    schedule = load_schedule()
    if args.trigger == "scheduled" and not schedule.get("enabled", True):
        print("Расписание выключено в config/schedule.yaml — выход")
        return

    criteria = load_yaml(ROOT / "config" / "criteria.yaml")
    raw_sources = load_yaml(ROOT / "config" / "sources.yaml")
    browser = raw_sources.get("browser", {})
    criteria["browser"] = browser

    init_db()
    session = get_session()
    errors: list[str] = []
    enriched = 0
    matched = 0
    scraped = 0

    if not args.skip_scan:
        print("=== Scan + Match ===")
        try:
            job = run_scheduled_update(
                session=session,
                match_limit=int(schedule.get("match_limit", 50)),
                trigger=args.trigger,
            )
            scraped = job.scraped
            matched = job.matched
            errors.extend(job.errors)
            print(
                f"Собрано {job.scraped} (новых {job.new_count}), "
                f"матчинг {job.matched}, run_id={job.run_id}"
            )
        except Exception as exc:
            errors.append(str(exc))
            print(f"⚠ scan/match failed: {exc}")

    if not args.skip_enrich:
        print("\n=== Enrich ===")
        limit = int(browser.get("enrich_limit", 30))
        min_score = int(criteria.get("thresholds", {}).get("min_score", 0))
        try:
            enriched, enrich_errors = enrich_vacancies(
                criteria=criteria,
                limit=limit,
                min_score=min_score,
                delay_seconds=float(browser.get("delay_seconds", 2)),
            )
            errors.extend(enrich_errors)
        except Exception as exc:
            errors.append(str(exc))
            print(f"⚠ enrich failed: {exc}")

    print("\n=== Analytics ===")
    try:
        analytics = build_analytics(session, criteria)
        snapshot = snapshot_for_today(analytics)
        save_daily_metrics(session, date.today().isoformat(), snapshot)

        export_path = ROOT / "data" / "dashboard.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(analytics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Экспорт: {export_path}")
    except Exception as exc:
        errors.append(f"analytics: {exc}")
        print(f"⚠ analytics failed: {exc}")

    session.close()

    print(
        f"\nГотово: собрано {scraped}, матчинг {matched}, обогащено {enriched}"
    )
    if errors:
        print("Ошибки:")
        for err in errors[:5]:
            print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
