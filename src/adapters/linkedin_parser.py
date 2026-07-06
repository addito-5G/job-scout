from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Callable

import requests

from models import Vacancy
from parsers.linkedin_jobs import (
    build_search_url,
    canonical_job_url,
    is_linkedin_job_url,
    parse_job_page,
    parse_search_fragment,
    vacancy_from_parsed,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

logger = logging.getLogger(__name__)


class LinkedinParserAdapter:
    """Публичный guest API LinkedIn Jobs — без логина и cookies пользователя."""

    name = "linkedin"
    progress_callback: Callable[[str], None] | None = None

    def __init__(
        self,
        queries: list[dict] | None = None,
        pages_per_query: int = 2,
        delay_seconds: float = 3.0,
        fetcher=None,
        *,
        location: str = "Russia",
        f_TPR: str = "r604800",
        remote_only: bool = False,
    ):
        self.queries = queries or [{"keywords": "product manager"}]
        self.pages_per_query = pages_per_query
        self.delay_seconds = delay_seconds
        self.fetcher = fetcher
        self.location = location
        self.f_TPR = f_TPR
        self.remote_only = remote_only
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                "Accept": "text/html,application/xhtml+xml",
            }
        )

    def _status(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    def _fetch_html(self, url: str) -> str:
        if self.fetcher:
            return self.fetcher.fetch(url)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_job_detail(self, job_id: str, fallback_url: str) -> dict | None:
        url = fallback_url or canonical_job_url(job_id)
        try:
            html = self._fetch_html(url)
            return parse_job_page(html, job_id=job_id)
        except Exception as exc:
            logger.warning("linkedin detail %s: %s", url, exc)
            return None

    def fetch(self) -> Iterator[Vacancy]:
        seen: set[str] = set()

        for query in self.queries:
            keywords = (query.get("keywords") or query.get("text") or "").strip()
            if not keywords:
                continue
            location = query.get("location") or self.location
            remote_only = bool(query.get("remote_only", self.remote_only))

            for page in range(self.pages_per_query):
                if page > 0:
                    time.sleep(self.delay_seconds)

                start = page * 25
                url = build_search_url(
                    keywords=keywords,
                    location=location,
                    start=start,
                    f_TPR=query.get("f_TPR") or self.f_TPR,
                    remote_only=remote_only,
                )
                self._status(f"поиск «{keywords}», стр. {page + 1}")

                try:
                    html = self._fetch_html(url)
                    cards = parse_search_fragment(html)
                except Exception as exc:
                    logger.warning("linkedin search «%s» p%s: %s", keywords, page, exc)
                    break

                if not cards:
                    break

                for card in cards:
                    job_id = card.get("external_id")
                    if not job_id or job_id in seen:
                        continue
                    seen.add(job_id)

                    self._status(f"карточка: {(card.get('title') or job_id)[:50]}")
                    detail = self._fetch_job_detail(job_id, card.get("url") or "")
                    if self.delay_seconds:
                        time.sleep(self.delay_seconds)

                    fields = vacancy_from_parsed(card, detail)
                    yield Vacancy(**fields)

                time.sleep(self.delay_seconds)


class LinkedinJobUrlAdapter:
    """Импорт одной вакансии по публичному URL (без авторизации)."""

    name = "linkedin"

    def __init__(self, url: str, *, delay_seconds: float = 0.0, fetcher=None):
        self.url = url
        self.delay_seconds = delay_seconds
        self.fetcher = fetcher
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _fetch_html(self, url: str) -> str:
        if self.fetcher:
            return self.fetcher.fetch(url)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def fetch(self) -> Iterator[Vacancy]:
        if not is_linkedin_job_url(self.url):
            return
        html = self._fetch_html(self.url)
        detail = parse_job_page(html)
        if not detail:
            raise RuntimeError(f"Не удалось разобрать вакансию LinkedIn: {self.url}")
        card = {
            "external_id": detail["external_id"],
            "title": detail.get("title") or "",
            "company": detail.get("company") or "",
            "location": detail.get("location") or "",
            "url": self.url,
        }
        yield Vacancy(**vacancy_from_parsed(card, detail))
