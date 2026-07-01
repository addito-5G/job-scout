from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Callable

from browser.fetcher import PageFetcher
from models import Vacancy
from parsers.geekjob_page import build_search_url, parse_search_page, parse_vacancy_page

logger = logging.getLogger(__name__)


class GeekjobParserAdapter:
    name = "geekjob"
    progress_callback: Callable[[str], None] | None = None

    def __init__(
        self,
        queries: list[str] | None = None,
        pages_per_query: int = 2,
        delay_seconds: float = 2.0,
        fetcher: PageFetcher | None = None,
    ):
        self.queries = queries or ["product manager", "продакт"]
        self.pages_per_query = pages_per_query
        self.delay_seconds = delay_seconds
        self.fetcher = fetcher

    def _status(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    def _fetch(self, url: str) -> str:
        if self.fetcher:
            return self.fetcher.fetch(url)
        import requests
        r = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
        )
        r.raise_for_status()
        return r.text

    def fetch(self) -> Iterator[Vacancy]:
        seen: set[str] = set()

        for query in self.queries:
            for page in range(1, self.pages_per_query + 1):
                if page > 1:
                    time.sleep(self.delay_seconds)
                url = build_search_url(query, page)
                self._status(f"поиск «{query}», страница {page}")
                try:
                    html = self._fetch(url)
                    items = parse_search_page(html)
                except Exception as exc:
                    logger.warning("geekjob ошибка %s p%s: %s", query, page, exc)
                    break

                if not items:
                    break

                for item in items:
                    eid = item["external_id"]
                    if eid in seen:
                        continue
                    seen.add(eid)

                    title_preview = (item.get("title") or "вакансия")[:50]
                    self._status(f"карточка: {title_preview}")

                    detail = None
                    try:
                        if self.delay_seconds > 0:
                            time.sleep(self.delay_seconds)
                        detail = parse_vacancy_page(self._fetch(item["url"]), url=item["url"])
                    except Exception as exc:
                        logger.warning("geekjob detail %s: %s", item["url"], exc)

                    if detail:
                        yield Vacancy(
                            source="geekjob",
                            external_id=eid,
                            title=detail.get("title") or item.get("title") or "Вакансия Geekjob",
                            company=detail.get("company") or "",
                            url=item["url"],
                            description_short=item.get("title") or detail.get("title") or "",
                            description_full=detail.get("full_description") or "",
                            skills=detail.get("skills") or [],
                            salary=detail.get("salary") or "",
                            location=detail.get("location") or "",
                            salary_min=detail.get("salary_min"),
                            salary_max=detail.get("salary_max"),
                            salary_currency=detail.get("salary_currency"),
                            work_format=detail.get("work_format"),
                            employment=detail.get("employment") or "",
                            published_at=detail.get("published_at"),
                        )
                    else:
                        yield Vacancy(
                            source="geekjob",
                            external_id=eid,
                            title=item.get("title") or "Вакансия Geekjob",
                            company="",
                            url=item["url"],
                            description_short=item.get("title") or "",
                        )

                time.sleep(self.delay_seconds)


def enrich_geekjob_vacancy(url: str, fetcher: PageFetcher) -> dict | None:
    html = fetcher.fetch(url)
    return parse_vacancy_page(html, url=url)
