"""Списки и агрегаты вакансий."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from db.models import Vacancy, VacancyTag
from db.repositories.vacancy_repo import get_vacancy_tags
from services.vacancy_queries import (
    build_count_by_source_query,
    build_list_vacancies_base,
    build_review_list_query,
    list_vacancy_filter_conditions,
)
from services.vacancy_service.types import VacancyFilters, VacancyListItem


def count_vacancies_by_source(session: Session, *, profile_role: str | None = None) -> dict[str, int]:
    rows = session.execute(build_count_by_source_query(profile_role=profile_role)).all()
    return {row[0]: int(row[1]) for row in rows}


def list_for_review(
    session: Session,
    *,
    min_score: int = 0,
    status: str | None = None,
    limit: int = 50,
) -> list[Vacancy]:
    query = build_review_list_query(min_score=min_score, status=status, limit=limit)
    return list(session.execute(query).scalars())


def get_salary_bounds(session: Session) -> tuple[int, int]:
    row = session.execute(
        select(
            func.min(Vacancy.salary_from),
            func.max(func.coalesce(Vacancy.salary_to, Vacancy.salary_from)),
        ).where(or_(Vacancy.salary_from.isnot(None), Vacancy.salary_to.isnot(None)))
    ).one()
    lo = int(row[0] or 0)
    hi = int(row[1] or 500_000)
    if hi <= lo:
        hi = max(lo + 100_000, 500_000)
    return lo, hi


def list_all_tags(session: Session, limit: int = 30) -> list[str]:
    rows = session.execute(
        select(VacancyTag.tag, func.count())
        .group_by(VacancyTag.tag)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return [r[0] for r in rows]


def list_vacancies(
    session: Session,
    profile_id: int | None,
    filters: VacancyFilters,
) -> tuple[list[VacancyListItem], int]:
    base, match_score_expr = build_list_vacancies_base(profile_id)
    conditions = list_vacancy_filter_conditions(
        filters, profile_id=profile_id, match_score_expr=match_score_expr
    )

    base = base.where(*conditions)
    total = session.execute(select(func.count()).select_from(base.subquery())).scalar_one()

    page = max(1, filters.page)
    offset = (page - 1) * filters.per_page
    rows = session.execute(
        base.order_by(match_score_expr.desc().nullslast(), Vacancy.rule_score.desc(), Vacancy.published_at.desc())
        .offset(offset)
        .limit(filters.per_page)
    ).all()

    items: list[VacancyListItem] = []
    for row in rows:
        v: Vacancy = row[0]
        tag_rows = get_vacancy_tags(session, v.id)
        items.append(
            VacancyListItem(
                id=v.id,
                title=v.title,
                company=row[1],
                salary=v.salary_text,
                salary_min=v.salary_from,
                salary_max=v.salary_to,
                work_format=v.work_format,
                location=v.location_text,
                match_score=int(row[2]) if row[2] is not None else None,
                recommendation=row[3],
                status=v.user_status or "new",
                url=v.external_url,
                score=v.rule_score or 0,
                published_at=v.published_at,
                tags=[t[0] for t in tag_rows],
                source=v.source,
            )
        )
    return items, total
