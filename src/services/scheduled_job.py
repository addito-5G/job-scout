from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from config_loader import load_criteria, load_sources
from db import get_session, init_db
from db.repositories.scan_repo import finish_scan_run, start_scan_run
from services.match_service import batch_fast_match
from services.profile_service import get_latest_profile
from services.scan_service import run_scan
from services.schedule_service import load_schedule
from services.search_service import get_active_search_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str, str | None], None]


@dataclass
class ScheduledJobResult:
    scraped: int = 0
    saved: int = 0
    new_count: int = 0
    matched: int = 0
    errors: list[str] = field(default_factory=list)
    run_id: int | None = None
    status: str = "completed"


def run_scheduled_update(
    *,
    session: Session | None = None,
    match_limit: int | None = None,
    progress: ProgressCallback | None = None,
    trigger: str = "manual",
) -> ScheduledJobResult:
    """Полный цикл: scan → match с записью в scan_runs."""
    owns_session = session is None
    if owns_session:
        init_db()
        session = get_session()

    schedule = load_schedule()
    match_limit = match_limit or int(schedule.get("match_limit", 50))
    result = ScheduledJobResult()
    run_id: int | None = None

    def _progress(value: float, message: str, source: str | None = None) -> None:
        if progress:
            progress(value, message, source)

    try:
        _progress(0.02, "Подготовка...", None)
        criteria = load_criteria()
        raw_sources = load_sources()
        min_score = int(criteria.get("thresholds", {}).get("min_score", 0))

        profile = get_latest_profile(session)
        if not profile or not profile.resume_raw:
            result.errors.append("Загрузите резюме перед обновлением")
            result.status = "failed"
            _progress(1.0, "Нужно резюме", None)
            return result

        settings = get_active_search_settings(session, profile.id)
        if not settings:
            result.errors.append("Настройте ключи поиска в разделе «Настройки»")
            result.status = "failed"
            _progress(1.0, "Нужны настройки поиска", None)
            return result

        run_id = start_scan_run(
            session,
            profile_id=profile.id,
            settings_id=settings.id,
        )
        result.run_id = run_id
        logger.info("Scheduled update started (trigger=%s, run_id=%s)", trigger, run_id)

        def scan_progress(frac: float, message: str, source: str | None = None) -> None:
            _progress(0.1 + frac * 0.45, message, source)

        _progress(0.1, "Сканирование источников...", None)
        scan = run_scan(session, criteria=criteria, raw_sources=raw_sources, progress=scan_progress)
        result.scraped = scan.scraped
        result.saved = scan.saved
        result.new_count = scan.new_count
        result.errors.extend(scan.errors)

        _progress(0.58, "AI-матчинг вакансий...", None)
        matched, match_errors = batch_fast_match(
            session,
            profile.id,
            limit=match_limit,
            min_score=min_score,
        )
        result.matched = matched
        result.errors.extend(match_errors)

        hh_found = int(scan.by_source.get("hh_parser", 0) + scan.by_source.get("hh", 0))
        habr_found = int(scan.by_source.get("habr", 0))
        geekjob_found = int(scan.by_source.get("geekjob", 0))

        finish_scan_run(
            session,
            run_id,
            scraped=result.scraped,
            new_count=result.new_count,
            updated=scan.updated_count,
            errors=len(result.errors),
            error_log="; ".join(result.errors[:10]),
            status="completed" if not result.errors else "completed_with_errors",
            hh_found=hh_found,
            habr_found=habr_found,
            geekjob_found=geekjob_found,
        )
        _progress(1.0, "Готово", None)
        return result
    except Exception as exc:
        session.rollback()
        logger.exception("scheduled update failed")
        result.errors.append(str(exc))
        result.status = "failed"
        if run_id:
            finish_scan_run(
                session,
                run_id,
                scraped=result.scraped,
                new_count=result.new_count,
                errors=len(result.errors) + 1,
                error_log=str(exc),
                status="failed",
            )
        raise
    finally:
        if owns_session and session is not None:
            session.close()


def scheduled_to_refresh(result: ScheduledJobResult):
    from services.refresh_service import RefreshResult

    return RefreshResult(
        scraped=result.scraped,
        saved=result.saved,
        new_count=result.new_count,
        matched=result.matched,
        errors=result.errors,
    )
