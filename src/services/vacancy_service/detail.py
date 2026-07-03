"""Детальная карточка вакансии."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import VacancyMatch
from db.repositories.vacancy_repo import get_vacancy_by_id, get_vacancy_skills, get_vacancy_tags
from services.vacancy_service.match_view import cover_letter_from_rows, match_to_dict
from services.vacancy_service.types import VacancyDetail


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
        cover_letter=cover_letter_from_rows(fast, deep),
        source=v.source,
        published_at=v.published_at,
        fast_match=match_to_dict(fast),
        deep_match=match_to_dict(deep),
    )
