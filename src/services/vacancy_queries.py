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
    """
    Базовый SELECT для списка вакансий с optional join на fast/deep match.

    rule_score — rule-based скоринг при скане (criteria.yaml).
    match_score — AI-скоринг из vacancy_matches (fast/deep).
    """
    fast = VacancyMatch.__table__.alias("fast_match")
    deep = VacancyMatch.__table__.alias("deep_match")

    if profile_id:
        match_score_expr = func.coalesce(deep.c.match_score, fast.c.match_score)
        base = (
            select(
                Vacancy,
                Company.name.label("company_name"),
                match_score_expr.label("match_score"),
                func.coalesce(deep.c.recommendation, fast.c.recommendation).label("recommendation"),
            )
            .outerjoin(Company, Company.id == Vacancy.company_id)
            .outerjoin(
                fast,
                (fast.c.vacancy_id == Vacancy.id)
                & (fast.c.profile_id == profile_id)
                & (fast.c.match_level == "fast"),
            )
            .outerjoin(
                deep,
                (deep.c.vacancy_id == Vacancy.id)
                & (deep.c.profile_id == profile_id)
                & (deep.c.match_level == "deep"),
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
    """Условия WHERE для list_vacancies (без изменения semantics фильтров)."""
    conditions: list[Any] = [Vacancy.is_active.is_(True)]
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
    if filters.profile_role is not None:
        conditions.append(Vacancy.profile_role == filters.profile_role)
    elif filters.search_settings_id is not None:
        conditions.append(Vacancy.search_settings_id == filters.search_settings_id)
    return conditions


def build_review_list_query(
    *,
    min_score: int = 0,
    status: str | None = None,
    limit: int = 50,
) -> Select:
    query = select(Vacancy).where(Vacancy.rule_score >= min_score, Vacancy.is_active.is_(True))
    if status:
        query = query.where(Vacancy.user_status == status)
    return query.order_by(Vacancy.rule_score.desc(), Vacancy.published_at.desc()).limit(limit)


def build_count_by_source_query(*, profile_role: str | None = None) -> Select:
    query = select(Vacancy.source, func.count()).where(
        Vacancy.is_active.is_(True), Vacancy.user_status != "hidden"
    )
    if profile_role is not None:
        query = query.where(Vacancy.profile_role == profile_role)
    return query.group_by(Vacancy.source)
