from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from config_loader import load_sources
from adapters.registry import build_adapters
from services.profile_service import get_active_profile
from services.scan_progress import ScanProgressFn, label_for
from services.search_service import get_active_search_settings, settings_to_queries
from services.vacancy_service import upsert_scored_vacancy
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = {
    "hh_parser": True,
}


@dataclass
class ScanResult:
    scraped: int = 0
    saved: int = 0
    new_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    matched_count: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    match_errors: list[str] = field(default_factory=list)
    pending_match_ids: list[int] = field(default_factory=list)


def _enabled_sources(settings) -> dict[str, bool]:
    if not settings or not settings.sources_enabled_json:
        return dict(DEFAULT_SOURCES)
    try:
        data = json.loads(settings.sources_enabled_json)
        if isinstance(data, dict):
            return {**DEFAULT_SOURCES, **{k: bool(v) for k, v in data.items() if k in DEFAULT_SOURCES}}
    except json.JSONDecodeError:
        pass
    return dict(DEFAULT_SOURCES)


def _apply_source_toggles(sources: dict, enabled: dict[str, bool]) -> dict:
    out = dict(sources)
    for key in ("hh_parser",):
        if key in out:
            out[key] = {**out[key], "enabled": enabled.get(key, out[key].get("enabled", True))}
    return out


def run_scan(
    session: Session,
    *,
    raw_sources: dict | None = None,
    manual_url: str | None = None,
    manual_title: str = "",
    manual_company: str = "",
    progress: ScanProgressFn | None = None,
    profile_id: int | None = None,
    run_match: bool = True,
    match_limit: int = 50,
) -> ScanResult:
    raw_sources = raw_sources or load_sources()
    sources_root = raw_sources.get("sources", raw_sources)
    browser = {**raw_sources.get("browser", {}), "engine": "requests", "use_for_scan": True}

    profile = None
    if profile_id is not None:
        from services.profile_service import get_profile

        profile = get_profile(session, profile_id)
    if profile is None:
        profile = get_active_profile(session)
    if not profile:
        if progress:
            progress(1.0, "Нет активного профиля резюме", None)
        return ScanResult()

    db_queries = None
    active_settings_id: int | None = None
    settings = get_active_search_settings(session, profile.id)
    if settings:
        active_settings_id = settings.id
        db_queries = settings_to_queries(settings)
        logger.info("Настройки из профиля #%s (settings #%s)", profile.id, settings.id)

    sources = _apply_source_toggles(sources_root, _enabled_sources(settings))

    adapters = build_adapters(
        sources,
        browser,
        db_queries=db_queries,
        manual_url=manual_url,
        manual_title=manual_title,
        manual_company=manual_company,
    )

    result = ScanResult()
    pending_match_ids: list[int] = []
    adapter_count = len(adapters)
    if adapter_count == 0:
        if progress:
            progress(1.0, "Нет активных источников", None)
        return result

    per_adapter = 0.85 / adapter_count

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

        logger.info("Сканирование: %s (профиль #%s)", adapter.name, profile.id)
        try:
            for raw in adapter.fetch():
                result.scraped += 1
                source_count += 1
                try:
                    vacancy_id, outcome = upsert_scored_vacancy(
                        session,
                        raw,
                        profile_id=profile.id,
                        search_settings_id=active_settings_id,
                    )
                except Exception as exc:
                    session.rollback()
                    msg = f"{adapter.name} #{raw.external_id}: {exc}"
                    result.errors.append(msg)
                    logger.warning(msg)
                    continue

                if outcome == "new":
                    result.saved += 1
                    result.new_count += 1
                elif outcome == "meta_updated":
                    result.saved += 1
                    result.updated_count += 1
                else:
                    result.skipped_count += 1

                if outcome in ("new", "meta_updated"):
                    pending_match_ids.append(vacancy_id)

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

        adapter_errors = getattr(adapter, "errors", None) or []
        for err in adapter_errors:
            if err not in result.errors:
                result.errors.append(err)

        result.by_source[adapter.name] = source_count
        if progress:
            progress(
                base_frac + per_adapter,
                f"{label}: готово ({source_count})",
                adapter.name,
            )

    result.pending_match_ids = list(dict.fromkeys(pending_match_ids))

    if run_match and (profile.resume_raw or profile.skills_json):
        from services.match_service import batch_fit_match

        if progress:
            progress(0.92, "Расчёт соответствия резюме…", None)

        matched, match_errors = batch_fit_match(
            session,
            profile.id,
            limit=match_limit,
            priority_vacancy_ids=result.pending_match_ids,
        )
        result.matched_count = matched
        result.match_errors = match_errors
        result.errors.extend(match_errors)

        if progress:
            progress(1.0, f"Соответствие: {matched} вакансий", None)

    return result
