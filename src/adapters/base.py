from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Callable

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
