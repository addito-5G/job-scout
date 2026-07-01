from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable

import feedparser

from models import Vacancy


class BaseAdapter(ABC):
    name: str
    progress_callback: Callable[[str], None] | None = None

    def _status(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    @abstractmethod
    def fetch(self) -> Iterator[Vacancy]:
        ...


class HabrRssAdapter(BaseAdapter):
    name = "habr_rss"

    def __init__(self, url: str):
        self.url = url

    def fetch(self) -> Iterator[Vacancy]:
        feed = feedparser.parse(self.url)

        for entry in feed.entries:
            published = None
            if getattr(entry, "published_parsed", None):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif getattr(entry, "updated_parsed", None):
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            company = ""
            if hasattr(entry, "author"):
                company = entry.author or ""

            yield Vacancy(
                source=self.name,
                external_id=entry.get("id", entry.link),
                title=entry.get("title", "").strip(),
                company=company,
                url=entry.link,
                description=entry.get("summary", ""),
                published_at=published,
            )


class ManualUrlAdapter(BaseAdapter):
    name = "manual"

    def __init__(self, url: str, title: str = "", company: str = "", description: str = ""):
        self.url = url
        self.title = title or "Вакансия (ручной ввод)"
        self.company = company
        self.description = description

    def fetch(self) -> Iterator[Vacancy]:
        yield Vacancy(
            source=self.name,
            external_id=self.url,
            title=self.title,
            company=self.company,
            url=self.url,
            description=self.description,
            published_at=datetime.now(timezone.utc),
        )
