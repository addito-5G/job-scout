#!/usr/bin/env python3
"""Ежедневное обновление: scan → match → analytics (для cron / launchd)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import config
from analytics import build_analytics, snapshot_for_today
from cli_logging import setup_cli_logging
from config_loader import load_criteria_with_browser
from db import get_session, init_db
from db.repositories.metrics_repo import save_daily_metrics
from enricher import enrich_vacancies
from services.scheduled_job import run_scheduled_update
from services.schedule_service import load_schedule

logger = setup_cli_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — daily update")
    parser.add_argument("--skip-scan", action="store_true", help="Пропустить scan+match")
    parser.add_argument("--skip-enrich", action="store_true")
    parser.add_argument("--trigger", default="scheduled", choices=["scheduled", "manual"])
    args = parser.parse_args()

    schedule = load_schedule()
    if args.trigger == "scheduled" and not schedule.get("enabled", True):
        logger.info("Расписание выключено в config/schedule.yaml — выход")
        return

    criteria = load_criteria_with_browser()
    browser = criteria.get("browser", {})

    init_db()
    session = get_session()
    errors: list[str] = []
    enriched = 0
    matched = 0
    scraped = 0

    if not args.skip_scan:
        logger.info("=== Scan + Match ===")
        try:
            job = run_scheduled_update(
                session=session,
                match_limit=int(schedule.get("match_limit", 50)),
                trigger=args.trigger,
            )
            scraped = job.scraped
            matched = job.matched
            errors.extend(job.errors)
            logger.info(
                f"Собрано {job.scraped} (новых {job.new_count}), "
                f"матчинг {job.matched}, run_id={job.run_id}"
            )
        except Exception as exc:
            errors.append(str(exc))
            logger.warning(f"scan/match failed: {exc}")

    if not args.skip_enrich:
        logger.info("\n=== Enrich ===")
        limit = int(browser.get("enrich_limit", 30))
        try:
            enriched, enrich_errors = enrich_vacancies(
                criteria=criteria,
                limit=limit,
                delay_seconds=float(browser.get("delay_seconds", 2)),
            )
            errors.extend(enrich_errors)
        except Exception as exc:
            errors.append(str(exc))
            logger.warning(f"enrich failed: {exc}")

    logger.info("\n=== Analytics ===")
    try:
        analytics = build_analytics(session, criteria)
        snapshot = snapshot_for_today(analytics)
        save_daily_metrics(session, date.today().isoformat(), snapshot)

        export_path = config.ROOT / "data" / "dashboard.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(analytics, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Экспорт: {export_path}")
    except Exception as exc:
        errors.append(f"analytics: {exc}")
        logger.warning(f"analytics failed: {exc}")

    session.close()

    logger.info(
        f"\nГотово: собрано {scraped}, матчинг {matched}, обогащено {enriched}"
    )
    if errors:
        logger.info("Ошибки:")
        for err in errors[:5]:
            logger.info(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
