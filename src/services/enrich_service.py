from __future__ import annotations

import logging
import time

from sqlalchemy.orm import Session

from adapters.geekjob_parser import enrich_geekjob_vacancy
from adapters.habr_parser import enrich_habr_vacancy
from browser.fetcher import PageFetcher, create_fetcher
from db.repositories.vacancy_repo import apply_enrichment, list_for_enrichment
from parsers.hh_state import extract_state, parse_vacancy_detail

logger = logging.getLogger(__name__)


def enrich_hh_vacancy(url: str, fetcher: PageFetcher) -> dict | None:
    html = fetcher.fetch(url)
    state = extract_state(html)
    if not state:
        return None
    detail = parse_vacancy_detail(state)
    if detail:
        detail["description_full"] = detail.get("full_description") or detail.get("description_full")
    return detail


def _enrich_by_source(source: str, url: str, fetcher: PageFetcher) -> dict | None:
    if source == "hh" or "hh.ru/vacancy/" in url:
        return enrich_hh_vacancy(url, fetcher)
    if source == "habr" or "career.habr.com/vacancies/" in url:
        return enrich_habr_vacancy(url, fetcher)
    if source == "geekjob" or "geekjob.ru/vacancy/" in url:
        return enrich_geekjob_vacancy(url, fetcher)
    return None


def enrich_vacancies_sa(
    session: Session,
    criteria: dict,
    limit: int = 50,
    delay_seconds: float = 2.0,
    fetcher: PageFetcher | None = None,
) -> tuple[int, list[str]]:
    owns_fetcher = fetcher is None
    if fetcher is None:
        browser_cfg = criteria.get("browser", {})
        fetcher = create_fetcher(
            engine=browser_cfg.get("engine", "auto"),
            headless=browser_cfg.get("headless", True),
            delay_seconds=browser_cfg.get("delay_seconds", 1.0),
        )

    rows = list_for_enrichment(session, limit=limit)
    enriched = 0
    errors: list[str] = []

    try:
        for row in rows:
            try:
                detail = _enrich_by_source(row.source, row.external_url, fetcher)
                if not detail:
                    errors.append(f"не поддерживается: {row.external_url}")
                    continue

                apply_enrichment(session, row, detail)
                enriched += 1
                logger.info("enriched #%s %s", row.id, row.title[:50])
            except Exception as exc:
                errors.append(f"{row.external_url}: {exc}")
                logger.warning("enrich failed %s: %s", row.external_url, exc)

            time.sleep(delay_seconds)
    finally:
        if owns_fetcher:
            fetcher.close()

    return enriched, errors
