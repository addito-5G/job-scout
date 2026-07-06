from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Vacancy:
    """DTO для парсеров вакансий."""

    source: str
    external_id: str
    title: str
    company: str = ""
    url: str = ""
    description: str = ""
    salary: str = ""
    location: str = ""
    published_at: Optional[datetime] = None
    user_status: str = "new"
    cover_letter: str = ""
    id: Optional[int] = None

    description_short: str = ""
    description_full: str = ""
    description_raw: dict[str, Any] | None = None
    skills: list[str] = field(default_factory=list)
    tags: list[tuple[str, str]] = field(default_factory=list)  # (tag, tag_type)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "RUR"
    salary_gross: Optional[bool] = None
    employment: str = ""
    work_schedule: str = ""
    experience: str = ""
    work_format: str | None = None
    enriched_at: Optional[datetime] = None

    company_external_id: str | None = None
    location_external_id: str | None = None
    company_logo_url: str | None = None

    # legacy aliases
    @property
    def full_description(self) -> str:
        return self.description_full

    @full_description.setter
    def full_description(self, value: str) -> None:
        self.description_full = value

    @property
    def status(self) -> str:
        return self.user_status

    @status.setter
    def status(self, value: str) -> None:
        self.user_status = value

    def skills_json(self) -> str:
        return json.dumps(self.skills, ensure_ascii=False)

    @staticmethod
    def skills_from_json(raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
