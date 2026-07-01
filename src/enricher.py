from __future__ import annotations

from browser.fetcher import PageFetcher


def enrich_vacancies(
    criteria: dict,
    limit: int = 50,
    min_score: int = 0,
    delay_seconds: float = 2.0,
    fetcher: PageFetcher | None = None,
) -> tuple[int, list[str]]:
    from db import get_session, init_db
    from services.enrich_service import enrich_vacancies_sa

    init_db()
    session = get_session()
    try:
        return enrich_vacancies_sa(
            session,
            criteria,
            limit=limit,
            min_score=min_score,
            delay_seconds=delay_seconds,
            fetcher=fetcher,
        )
    finally:
        session.close()
