from __future__ import annotations

import logging
import time
from collections.abc import Iterator
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

logger = logging.getLogger(__name__)


class HhParserAdapter:
    name = "hh_parser"
    progress_callback: Callable[[str], None] | None = None

    def __init__(
        self,
        queries: list[dict],
        pages_per_query: int = 2,
        delay_seconds: float = 2.0,
        fetcher=None,
    ):
        self.queries = queries
        self.pages_per_query = pages_per_query
        self.delay_seconds = delay_seconds
        self.fetcher = fetcher
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ru-RU,ru;q=0.9"})

    def _status(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

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
            raise RuntimeError(f"Не удалось разобрать HH-Lux-InitialState: {url}")
        return find_vacancy_list(state) or []

    def fetch(self) -> Iterator[Vacancy]:
        seen: set[str] = set()

        for q in self.queries:
            params = {
                "text": q.get("text", "product manager"),
                "area": q.get("area", 1),
                "search_field": q.get("search_field", "name"),
            }
            if q.get("schedule"):
                params["schedule"] = q["schedule"]

            for page in range(self.pages_per_query):
                if page > 0:
                    time.sleep(self.delay_seconds)

                query_text = params["text"]
                self._status(f"поиск «{query_text}», страница {page + 1}")

                try:
                    items = self._fetch_page(params, page)
                except Exception as exc:
                    logger.warning("hh ошибка %s p%s: %s", params["text"], page, exc)
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
                        published_at=(detail or {}).get("published_at") or parsed["published_at"],
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
