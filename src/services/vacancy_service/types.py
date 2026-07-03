"""DTO для списков и детальной карточки вакансии."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VacancyFilters:
    """Фильтры списка вакансий.

    Скоринг:
    - ``min_match_score`` — порог AI-match (``vacancy_matches.match_score``, fast/deep).
    - Поле ``score`` в ``VacancyListItem`` — rule-based ``Vacancy.rule_score`` из criteria.yaml при скане.
    """

    salary_min: int | None = None
    salary_max: int | None = None
    work_formats: list[str] | None = None
    min_match_score: int = 0
    search: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    search_settings_id: int | None = None
    profile_role: str | None = None
    user_status: str | None = None
    hide_hidden: bool = True
    page: int = 1
    per_page: int = 30


@dataclass
class VacancyListItem:
    id: int
    title: str
    company: str | None
    salary: str | None
    salary_min: int | None
    salary_max: int | None
    work_format: str | None
    location: str | None
    match_score: int | None
    recommendation: str | None
    status: str
    url: str
    score: int  # rule_score (criteria.yaml), не AI match_score
    published_at: datetime | None
    tags: list[str]
    source: str = ""


@dataclass
class VacancyDetail:
    id: int
    title: str
    company: str | None
    company_description: str | None
    company_website: str | None
    url: str
    description: str | None
    full_description: str | None
    skills: list[str]
    tags: list[tuple[str, str | None]]
    salary: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    location: str | None
    work_format: str | None
    employment: str | None
    experience: str | None
    status: str
    score: int  # rule_score (criteria.yaml)
    cover_letter: str | None
    source: str
    published_at: datetime | None
    fast_match: dict | None
    deep_match: dict | None
