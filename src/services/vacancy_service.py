from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, not_, or_, select
from sqlalchemy.orm import Session

from db.models import Company, Skill, Vacancy, VacancyMatch, VacancySkill, VacancyTag
from db.repositories.vacancy_repo import get_vacancy_by_id, get_vacancy_skills, get_vacancy_tags, upsert_vacancy
from models import Vacancy as VacancyDTO


@dataclass
class VacancyFilters:
    salary_min: int | None = None
    salary_max: int | None = None
    work_formats: list[str] | None = None
    min_match_score: int = 0
    search: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    search_settings_id: int | None = None
    profile_role: str | None = None
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
    score: int
    published_at: datetime | None
    tags: list[str]


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
    score: int
    cover_letter: str | None
    source: str
    published_at: datetime | None
    fast_match: dict | None
    deep_match: dict | None


def upsert_scored_vacancy(
    session: Session,
    vacancy: VacancyDTO,
    *,
    search_settings_id: int | None = None,
) -> tuple[int, bool]:
    return upsert_vacancy(session, vacancy, search_settings_id=search_settings_id)


def count_vacancies_by_source(session: Session, *, profile_role: str | None = None) -> dict[str, int]:
    query = select(Vacancy.source, func.count()).where(
        Vacancy.is_active.is_(True), Vacancy.user_status != "hidden"
    )
    if profile_role is not None:
        query = query.where(Vacancy.profile_role == profile_role)
    rows = session.execute(query.group_by(Vacancy.source)).all()
    return {row[0]: int(row[1]) for row in rows}


def list_for_review(
    session: Session,
    *,
    min_score: int = 0,
    status: str | None = None,
    limit: int = 50,
) -> list[Vacancy]:
    query = select(Vacancy).where(Vacancy.rule_score >= min_score, Vacancy.is_active.is_(True))
    if status:
        query = query.where(Vacancy.user_status == status)
    query = query.order_by(Vacancy.rule_score.desc(), Vacancy.published_at.desc()).limit(limit)
    return list(session.execute(query).scalars())


def _match_to_dict(row: VacancyMatch | None) -> dict | None:
    if not row:
        return None

    def loads(raw: str | None) -> list:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    return {
        "match_score": int(row.match_score or 0),
        "match_summary": row.recommendation_reason or (row.ai_analysis or "")[:500],
        "matched_skills": loads(row.matched_skills_json),
        "missing_skills": loads(row.missing_skills_json),
        "strengths": loads(row.strengths_for_vacancy_json),
        "risks": loads(row.risks_json),
        "recommendation": row.recommendation,
        "deep_analysis": row.ai_analysis,
        "cover_letter_draft": row.cover_letter_draft,
    }


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

    conditions = [Vacancy.is_active.is_(True)]
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
    if filters.profile_role is not None:
        conditions.append(Vacancy.profile_role == filters.profile_role)
    elif filters.search_settings_id is not None:
        conditions.append(Vacancy.search_settings_id == filters.search_settings_id)

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
            )
        )
    return items, total


def get_vacancy_detail(
    session: Session,
    vacancy_id: int,
    profile_id: int | None,
) -> VacancyDetail | None:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return None

    fast = deep = None
    if profile_id:
        fast = session.execute(
            select(VacancyMatch).where(
                VacancyMatch.vacancy_id == vacancy_id,
                VacancyMatch.profile_id == profile_id,
                VacancyMatch.match_level == "fast",
            )
        ).scalar_one_or_none()
        deep = session.execute(
            select(VacancyMatch).where(
                VacancyMatch.vacancy_id == vacancy_id,
                VacancyMatch.profile_id == profile_id,
                VacancyMatch.match_level == "deep",
            )
        ).scalar_one_or_none()

    skills = get_vacancy_skills(session, vacancy_id)
    tags = get_vacancy_tags(session, vacancy_id)
    company = v.company_rel

    return VacancyDetail(
        id=v.id,
        title=v.title,
        company=company.name if company else None,
        company_description=company.description if company else None,
        company_website=company.website if company else None,
        url=v.external_url,
        description=v.description_short,
        full_description=v.description_full,
        skills=skills,
        tags=tags,
        salary=v.salary_text,
        salary_min=v.salary_from,
        salary_max=v.salary_to,
        salary_currency=v.salary_currency,
        location=v.location_text,
        work_format=v.work_format,
        employment=v.employment,
        experience=v.experience_required,
        status=v.user_status or "new",
        score=v.rule_score or 0,
        cover_letter=deep.cover_letter_draft if deep and deep.cover_letter_draft else None,
        source=v.source,
        published_at=v.published_at,
        fast_match=_match_to_dict(fast),
        deep_match=_match_to_dict(deep),
    )


def update_vacancy_status(session: Session, vacancy_id: int, status: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    v.user_status = status
    v.updated_at = datetime.utcnow()
    session.commit()
    return True


def save_vacancy_cover_letter(session: Session, vacancy_id: int, letter: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    if v.matches:
        for m in v.matches:
            if m.match_level == "deep":
                m.cover_letter_draft = letter
    session.commit()
    return True


def count_new_vacancies(session: Session, days: int) -> int:
    since = datetime.utcnow() - timedelta(days=days)
    return session.execute(
        select(func.count())
        .select_from(Vacancy)
        .where(or_(Vacancy.published_at >= since, Vacancy.scraped_at >= since))
    ).scalar_one()
