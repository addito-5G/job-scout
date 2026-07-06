"""Сервис вакансий — публичный API (re-export подмодулей)."""

from services.vacancy_service.company_listing import get_company_detail, list_companies
from services.vacancy_service.detail import get_vacancy_detail
from services.vacancy_service.listing import (
    count_vacancies_by_source,
    get_salary_bounds,
    list_all_tags,
    list_for_review,
    list_vacancies,
)
from services.vacancy_service.match_view import match_has_analysis, pick_best_match
from services.vacancy_service.types import (
    CompanyDetail,
    CompanyListItem,
    VacancyDetail,
    VacancyFilters,
    VacancyListItem,
)
from services.vacancy_service.write import (
    save_vacancy_cover_letter,
    update_vacancy_status,
    upsert_scored_vacancy,
)

__all__ = [
    "CompanyDetail",
    "CompanyListItem",
    "VacancyDetail",
    "VacancyFilters",
    "VacancyListItem",
    "count_vacancies_by_source",
    "get_company_detail",
    "get_salary_bounds",
    "get_vacancy_detail",
    "list_all_tags",
    "list_companies",
    "list_for_review",
    "list_vacancies",
    "match_has_analysis",
    "pick_best_match",
    "save_vacancy_cover_letter",
    "update_vacancy_status",
    "upsert_scored_vacancy",
]
