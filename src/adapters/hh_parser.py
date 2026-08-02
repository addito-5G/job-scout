from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Callable
from urllib.parse import urlencode

import requests

from models import Vacancy
from parsers.hh_state import (
    extract_state,
    find_vacancy_list,
    parse_search_item,
    parse_vacancy_detail,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
SEARCH_URL = "https://hh.ru/search/vacancy"
DEFAULT_SEARCH_PERIOD_DAYS = 7

logger = logging.getLogger(__name__)


class HhParserAdapter:
    name = "hh_parser"
    progress_callback: Callable[[str], None] | None = None

    def __init__(
        self,
        queries: list[dict],
        pages_per_query: int = 2,
        delay_seconds: float = 2.0,
        search_period: int = DEFAULT_SEARCH_PERIOD_DAYS,
        fetcher=None,
    ):
        self.queries = queries
        self.pages_per_query = pages_per_query
        self.delay_seconds = delay_seconds
        self.search_period = max(0, int(search_period))
        self.fetcher = fetcher
        self.errors: list[str] = []
        self.skipped_old = 0
        self.kept_undated = 0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ru-RU,ru;q=0.9"})

    def _status(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    def _search_params(self, q: dict) -> dict:
        period = int(q.get("search_period", self.search_period))
        params = {
            "text": q.get("text", "product manager"),
            "area": q.get("area", 1),
            "search_field": q.get("search_field", "name"),
            "order_by": "publication_time",
        }
        if period > 0:
            params["search_period"] = period
        if q.get("schedule"):
            params["schedule"] = q["schedule"]
        return params

    def _within_period(self, published_at: datetime | None, period_days: int) -> bool:
        """Client-side age filter. Undated rows are kept when HH already got search_period."""
        if period_days <= 0:
            return True
        if published_at is None:
            # HH URL already constrained by search_period; dropping undated loses valid cards
            # when search snippets omit publicationTime and detail enrich failed/skipped.
            self.kept_undated += 1
            return True
        pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        if pub >= cutoff:
            return True
        self.skipped_old += 1
        return False

    def _fetch_html(self, url: str) -> str:
        if self.fetcher:
            return self.fetcher.fetch(url)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_page(self, params: dict, page: int) -> list[dict]:
        query = {**params, "page": page}
        url = f"{SEARCH_URL}?{urlencode(query)}"
        html = self._fetch_html(url)
        state = extract_state(html)
        if not state:
            lowered = html.lower()
            if "доступ ограничен" in lowered or "captcha-form" in lowered:
                raise RuntimeError(f"HH блок/captcha вместо выдачи: {url}")
            raise RuntimeError(f"Не удалось разобрать HH-Lux-InitialState: {url}")
        return find_vacancy_list(state) or []

    def fetch(self) -> Iterator[Vacancy]:
        seen: set[str] = set()

        for q in self.queries:
            params = self._search_params(q)
            period_days = int(params.get("search_period", 0) or 0)

            for page in range(self.pages_per_query):
                if page > 0:
                    time.sleep(self.delay_seconds)

                query_text = params["text"]
                self._status(f"поиск «{query_text}», страница {page + 1}")

                try:
                    items = self._fetch_page(params, page)
                except Exception as exc:
                    msg = f"hh ошибка «{params['text']}» p{page}: {exc}"
                    self.errors.append(msg)
                    logger.warning(msg)
                    break

                if not items:
                    break

                for item in items:
                    parsed = parse_search_item(item)
                    vid = parsed["external_id"]
                    if not vid or vid in seen:
                        continue
                    seen.add(vid)

                    snippet_parts = [
                        parsed["title"],
                        parsed["company"],
                        parsed["location"],
                        parsed["salary"],
                        parsed["experience"],
                        parsed["employment"],
                    ]
                    desc_short = " | ".join(p for p in snippet_parts if p)

                    detail = None
                    if self.fetcher:
                        self._status(f"карточка: {parsed['title'][:50]}")
                        try:
                            html = self._fetch_html(parsed["url"])
                            state = extract_state(html)
                            if state:
                                detail = parse_vacancy_detail(state)
                                time.sleep(self.delay_seconds)
                        except Exception as exc:
                            logger.warning("hh detail %s: %s", parsed["url"], exc)

                    published_at = (detail or {}).get("published_at") or parsed["published_at"]
                    if not self._within_period(published_at, period_days):
                        continue

                    yield Vacancy(
                        source="hh",
                        external_id=vid,
                        title=(detail or {}).get("title") or parsed["title"],
                        company=(detail or {}).get("company") or parsed["company"],
                        url=parsed["url"],
                        description_short=desc_short,
                        description_full=(detail or {}).get("full_description") or "",
                        salary=(detail or {}).get("salary") or parsed["salary"],
                        location=(detail or {}).get("location") or parsed["location"],
                        published_at=published_at,
                        skills=(detail or {}).get("skills") or parsed["skills"],
                        salary_min=(detail or {}).get("salary_min") if detail else parsed["salary_min"],
                        salary_max=(detail or {}).get("salary_max") if detail else parsed["salary_max"],
                        salary_currency=parsed["salary_currency"],
                        salary_gross=parsed["salary_gross"],
                        employment=(detail or {}).get("employment") or parsed["employment"],
                        work_schedule=(detail or {}).get("work_schedule") or parsed["work_schedule"],
                        experience=(detail or {}).get("experience") or parsed["experience"],
                    )

                time.sleep(self.delay_seconds)

        if self.kept_undated or self.skipped_old:
            logger.info(
                "hh period filter: kept_undated=%s skipped_old=%s",
                self.kept_undated,
                self.skipped_old,
            )
