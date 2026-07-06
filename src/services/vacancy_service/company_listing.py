"""Списки компаний-работодателей с агрегацией вакансий профиля."""

from __future__ import annotations

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from db.models import Company, Vacancy, VacancyMatch
from services.company_brief_service import ensure_company_brief
from services.vacancy_queries import (
    build_list_vacancies_base,
    list_vacancy_filter_conditions,
)
from services.vacancy_service.types import CompanyDetail, CompanyListItem, VacancyFilters


def _company_group_query(profile_id: int | None) -> tuple[select, ColumnElement]:
    fit = VacancyMatch.__table__.alias("fit_match_co")
    legacy_deep = VacancyMatch.__table__.alias("legacy_deep_match_co")
    legacy_fast = VacancyMatch.__table__.alias("legacy_fast_match_co")

    if profile_id:
        match_score_expr: ColumnElement = func.coalesce(
            fit.c.match_score,
            legacy_deep.c.match_score,
            legacy_fast.c.match_score,
        )
        query = (
            select(
                Company.id,
                Company.name,
                Company.ai_brief,
                Company.website,
                func.count(Vacancy.id).label("vacancy_count"),
                func.max(match_score_expr).label("best_match"),
                func.group_concat(func.distinct(Vacancy.source)).label("sources_csv"),
            )
            .select_from(Vacancy)
            .join(Company, Company.id == Vacancy.company_id)
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
        match_score_expr = literal(None)
        query = (
            select(
                Company.id,
                Company.name,
                Company.ai_brief,
                Company.website,
                func.count(Vacancy.id).label("vacancy_count"),
                literal(None).label("best_match"),
                func.group_concat(func.distinct(Vacancy.source)).label("sources_csv"),
            )
            .select_from(Vacancy)
            .join(Company, Company.id == Vacancy.company_id)
        )

    return query, match_score_expr


def list_companies(
    session: Session,
    profile_id: int | None,
    filters: VacancyFilters,
) -> tuple[list[CompanyListItem], int]:
    _, match_score_expr = build_list_vacancies_base(profile_id)
    conditions = list_vacancy_filter_conditions(
        filters, profile_id=profile_id, match_score_expr=match_score_expr
    )
    conditions.append(Company.id.isnot(None))

    grouped, order_match_expr = _company_group_query(profile_id)
    grouped = grouped.where(*conditions).group_by(Company.id)

    total = session.execute(select(func.count()).select_from(grouped.subquery())).scalar_one()

    page = max(1, filters.page)
    offset = (page - 1) * filters.per_page
    rows = session.execute(
        grouped.order_by(
            order_match_expr.desc().nullslast(),
            func.count(Vacancy.id).desc(),
            Company.name.asc(),
        )
        .offset(offset)
        .limit(filters.per_page)
    ).all()

    items: list[CompanyListItem] = []
    for row in rows:
        sources_raw = (row.sources_csv or "").split(",") if row.sources_csv else []
        sources = list(dict.fromkeys(s.strip() for s in sources_raw if s.strip()))
        items.append(
            CompanyListItem(
                id=row.id,
                name=row.name,
                ai_brief=row.ai_brief,
                website=row.website,
                vacancy_count=int(row.vacancy_count or 0),
                best_match_score=int(row.best_match) if row.best_match is not None else None,
                sources=sources,
            )
        )
    return items, int(total)


def get_company_detail(
    session: Session,
    company_id: int,
    profile_id: int | None,
    *,
    ensure_brief: bool = True,
) -> CompanyDetail | None:
    company = session.get(Company, company_id)
    if not company:
        return None

    conditions = [
        Vacancy.is_active.is_(True),
        Vacancy.user_status != "hidden",
        Vacancy.company_id == company_id,
    ]
    if profile_id is not None:
        conditions.append(Vacancy.profile_id == profile_id)

    fit = VacancyMatch.__table__.alias("fit_match_cd")
    legacy_deep = VacancyMatch.__table__.alias("legacy_deep_match_cd")
    legacy_fast = VacancyMatch.__table__.alias("legacy_fast_match_cd")
    if profile_id:
        ms_expr = func.coalesce(
            fit.c.match_score,
            legacy_deep.c.match_score,
            legacy_fast.c.match_score,
        )
        count_query = (
            select(func.count(Vacancy.id), func.max(ms_expr))
            .select_from(Vacancy)
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
            .where(*conditions)
        )
    else:
        count_query = select(func.count(Vacancy.id), literal(None)).select_from(Vacancy).where(
            *conditions
        )

    count_row = session.execute(count_query).one()
    vacancy_count = int(count_row[0] or 0)
    best_match = int(count_row[1]) if count_row[1] is not None else None

    if ensure_brief and not company.ai_brief and vacancy_count > 0:
        top_vac = session.execute(
            select(Vacancy)
            .where(*conditions)
            .order_by(Vacancy.published_at.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()
        if top_vac:
            snippet = top_vac.description_full or top_vac.description_short or ""
            ensure_company_brief(
                session,
                company,
                vacancy_snippet=snippet,
                source=top_vac.source,
            )
            session.refresh(company)

    return CompanyDetail(
        id=company.id,
        name=company.name,
        ai_brief=company.ai_brief,
        website=company.website,
        description=company.description,
        vacancy_count=vacancy_count,
        best_match_score=best_match,
    )
