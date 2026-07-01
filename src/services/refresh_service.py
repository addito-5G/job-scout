from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from typing import Callable

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str, str | None], None]


@dataclass
class RefreshResult:
    scraped: int = 0
    saved: int = 0
    new_count: int = 0
    matched: int = 0
    errors: list[str] = field(default_factory=list)


def refresh_vacancies(
    *,
    match_limit: int = 50,
    min_score: int | None = None,
    progress: ProgressCallback | None = None,
) -> RefreshResult:
    """Сканирование + fast match (UI и ручной запуск)."""
    del min_score  # порог берётся из criteria.yaml внутри scheduled_job
    from services.scheduled_job import run_scheduled_update, scheduled_to_refresh

    try:
        job = run_scheduled_update(match_limit=match_limit, progress=progress, trigger="manual")
        return scheduled_to_refresh(job)
    except Exception:
        logger.exception("refresh_vacancies failed")
        raise
