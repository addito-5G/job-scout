"""SQLAlchemy query builders для списков и агрегатов вакансий."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, or_, select
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

from db.models import Company, Vacancy, VacancyMatch, VacancyTag

if TYPE_CHECKING:
    from services.vacancy_service import VacancyFilters


def build_list_vacancies_base(profile_id: int | None) -> tuple[Select, ColumnElement]:
    """Базовый SELECT для списка вакансий с join на единый fit match."""
    fit = VacancyMatch.__table__.alias("fit_match")
    legacy_deep = VacancyMatch.__table__.alias("legacy_deep_match")
    legacy_fast = VacancyMatch.__table__.alias("legacy_fast_match")

    if profile_id:
        match_score_expr = func.coalesce(
            fit.c.match_score,
            legacy_deep.c.match_score,
            legacy_fast.c.match_score,
        )
        recommendation_expr = func.coalesce(
            fit.c.recommendation,
            legacy_deep.c.recommendation,
            legacy_fast.c.recommendation,
        )
        base = (
            select(
                Vacancy,
                Company.name.label("company_name"),
                match_score_expr.label("match_score"),
                recommendation_expr.label("recommendation"),
            )
            .outerjoin(Company, Company.id == Vacancy.company_id)
            .outerjoin(
                fit,
                (fit.c.vacancy_id == Vacancy.id)
                & (fit.c.profile_id == profile_id)
                & (fit.c.match_level == "fit"),
            )
            .outerjoin(
                legacy_deep,
                (legacy_deep.c.vacancy_id == Vacancy.id)
                & (legacy_deep.c.profile_id == profile_id)
                & (legacy_deep.c.match_level == "deep"),
            )
            .outerjoin(
                legacy_fast,
                (legacy_fast.c.vacancy_id == Vacancy.id)
                & (legacy_fast.c.profile_id == profile_id)
                & (legacy_fast.c.match_level == "fast"),
            )
        )
    else:
        match_score_expr = func.literal(0)
        base = (
            select(
                Vacancy,
                Company.name.label("company_name"),
                func.literal(None).label("match_score"),
                func.literal(None).label("recommendation"),
            )
            .outerjoin(Company, Company.id == Vacancy.company_id)
        )

    return base, match_score_expr


def list_vacancy_filter_conditions(
    filters: VacancyFilters,
    *,
    profile_id: int | None,
    match_score_expr: ColumnElement,
) -> list[Any]:
    """Условия WHERE для list_vacancies."""
    conditions: list[Any] = [Vacancy.is_active.is_(True)]
    if profile_id is not None:
        conditions.append(Vacancy.profile_id == profile_id)
    if filters.hide_hidden:
        conditions.append(Vacancy.user_status != "hidden")
    if filters.work_formats:
        conditions.append(Vacancy.work_format.in_(filters.work_formats))
    if filters.search:
        q = f"%{filters.search.strip()}%"
        conditions.append(or_(Vacancy.title.ilike(q), Company.name.ilike(q)))
    if filters.salary_min is not None:
        conditions.append(or_(Vacancy.salary_to.is_(None), Vacancy.salary_to >= filters.salary_min))
    if filters.salary_max is not None:
        conditions.append(or_(Vacancy.salary_from.is_(None), Vacancy.salary_from <= filters.salary_max))
    if filters.min_match_score > 0 and profile_id is not None:
        conditions.append(match_score_expr >= filters.min_match_score)
    if filters.tags:
        tag_subq = (
            select(VacancyTag.vacancy_id)
            .where(VacancyTag.tag.in_(filters.tags))
            .group_by(VacancyTag.vacancy_id)
            .having(func.count(VacancyTag.id) >= 1)
        )
        conditions.append(Vacancy.id.in_(tag_subq))
    if filters.source:
        conditions.append(Vacancy.source == filters.source)
    if filters.user_status:
        conditions.append(Vacancy.user_status == filters.user_status)
    if filters.company_id is not None:
        conditions.append(Vacancy.company_id == filters.company_id)
    if filters.profile_role is not None:
        conditions.append(Vacancy.profile_role == filters.profile_role)
    elif filters.search_settings_id is not None:
        conditions.append(Vacancy.search_settings_id == filters.search_settings_id)
    return conditions


def build_review_list_query(
    *,
    status: str | None = None,
    limit: int = 50,
) -> Select:
    query = select(Vacancy).where(Vacancy.is_active.is_(True))
    if status:
        query = query.where(Vacancy.user_status == status)
    return query.order_by(Vacancy.published_at.desc().nullslast(), Vacancy.updated_at.desc()).limit(limit)


def build_count_by_source_query(*, profile_id: int | None = None) -> Select:
    query = select(Vacancy.source, func.count()).where(
        Vacancy.is_active.is_(True), Vacancy.user_status != "hidden"
    )
    if profile_id is not None:
        query = query.where(Vacancy.profile_id == profile_id)
    return query.group_by(Vacancy.source)
