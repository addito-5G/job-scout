"""DTO для списков и детальной карточки вакансии."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VacancyFilters:
    """Фильтры списка вакансий."""

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
    company_id: int | None = None


@dataclass
class CompanyListItem:
    id: int
    name: str
    ai_brief: str | None
    website: str | None
    vacancy_count: int
    best_match_score: int | None
    sources: list[str]


@dataclass
class CompanyDetail:
    id: int
    name: str
    ai_brief: str | None
    website: str | None
    description: str | None
    vacancy_count: int
    best_match_score: int | None


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
    cover_letter: str | None
    source: str
    published_at: datetime | None
    fit_match: dict | None
