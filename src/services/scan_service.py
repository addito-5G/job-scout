from __future__ import annotations

import logging
from dataclasses import dataclass, field

from config_loader import load_criteria, load_sources
from adapters.registry import build_adapters
from scoring import score_vacancy
from services.profile_service import get_latest_profile
from services.scan_progress import ScanProgressFn, label_for
from services.search_service import get_active_search_settings, settings_to_habr_queries, settings_to_queries
from services.vacancy_service import upsert_scored_vacancy
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    scraped: int = 0
    saved: int = 0
    new_count: int = 0
    updated_count: int = 0
    priority_count: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def run_scan(
    session: Session,
    *,
    criteria: dict | None = None,
    raw_sources: dict | None = None,
    manual_url: str | None = None,
    manual_title: str = "",
    manual_company: str = "",
    display_min: int | None = None,
    progress: ScanProgressFn | None = None,
) -> ScanResult:
    criteria = criteria or load_criteria()
    raw_sources = raw_sources or load_sources()
    sources = raw_sources.get("sources", raw_sources)
    browser = raw_sources.get("browser", {})

    display_min = display_min if display_min is not None else criteria.get("thresholds", {}).get("min_score", 55)
    priority = criteria.get("thresholds", {}).get("priority_score", 70)

    profile = get_latest_profile(session)
    db_queries = None
    habr_queries = None
    geekjob_queries = None
    active_settings_id: int | None = None
    if profile:
        settings = get_active_search_settings(session, profile.id)
        if settings:
            active_settings_id = settings.id
            db_queries = settings_to_queries(settings)
            habr_queries = settings_to_habr_queries(settings)
            geekjob_queries = settings_to_habr_queries(settings)
            logger.info("Настройки из профиля #%s (settings #%s)", profile.id, settings.id)

    if habr_queries and sources.get("habr_parser"):
        sources = {**sources, "habr_parser": {**sources.get("habr_parser", {}), "queries": habr_queries}}
    if geekjob_queries and sources.get("geekjob_parser"):
        sources = {**sources, "geekjob_parser": {**sources.get("geekjob_parser", {}), "queries": geekjob_queries}}

    adapters = build_adapters(
        sources,
        browser,
        db_queries=db_queries,
        manual_url=manual_url,
        manual_title=manual_title,
        manual_company=manual_company,
    )

    result = ScanResult()
    adapter_count = len(adapters)
    if adapter_count == 0:
        if progress:
            progress(1.0, "Нет активных источников", None)
        return result

    per_adapter = 1.0 / adapter_count

    for adapter_index, adapter in enumerate(adapters):
        label = label_for(adapter.name)
        base_frac = adapter_index * per_adapter
        source_count = 0

        def adapter_status(msg: str, *, _base=base_frac, _pa=per_adapter, _name=adapter.name) -> None:
            if progress:
                progress(_base + _pa * 0.05, f"{label}: {msg}", _name)

        adapter.progress_callback = adapter_status

        if progress:
            progress(base_frac, f"Старт — {label}", adapter.name)

        logger.info("Сканирование: %s", adapter.name)
        try:
            for raw in adapter.fetch():
                result.scraped += 1
                source_count += 1
                scored = score_vacancy(raw, criteria)
                try:
                    _, is_new = upsert_scored_vacancy(
                        session, scored, search_settings_id=active_settings_id
                    )
                except Exception as exc:
                    session.rollback()
                    msg = f"{adapter.name} #{raw.external_id}: {exc}"
                    result.errors.append(msg)
                    logger.warning(msg)
                    continue

                result.saved += 1
                if is_new:
                    result.new_count += 1
                else:
                    result.updated_count += 1
                if scored.score >= priority:
                    result.priority_count += 1

                if progress:
                    sub = min(0.95, source_count / max(source_count + 5, 40))
                    progress(
                        base_frac + per_adapter * sub,
                        f"{label}: сохранено {source_count}",
                        adapter.name,
                    )
        except Exception as exc:
            session.rollback()
            msg = f"{adapter.name}: {exc}"
            result.errors.append(msg)
            logger.warning(msg)

        result.by_source[adapter.name] = source_count
        if progress:
            progress(
                base_frac + per_adapter,
                f"{label}: готово ({source_count})",
                adapter.name,
            )

    return result
