"""Сервис матчинга: единый детерминированный fit score."""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from db.models import CandidateProfile, Vacancy
from db.repositories.match_repo import upsert_match
from db.repositories.vacancy_repo import get_vacancy_skills, list_for_matching
from domain.fit_score import fit_from_profile_model, fit_to_match_dict
from services.profile_service import get_active_profile

logger = logging.getLogger(__name__)

MATCH_LEVEL = "fit"


def vacancy_to_json(session: Session, vacancy: Vacancy) -> str:
    skills = get_vacancy_skills(session, vacancy.id)
    data = {
        "title": vacancy.title,
        "company": vacancy.company_rel.name if vacancy.company_rel else None,
        "description": vacancy.description_full or vacancy.description_short,
        "skills": skills,
        "salary": vacancy.salary_text,
        "salary_min": vacancy.salary_from,
        "salary_max": vacancy.salary_to,
        "location": vacancy.location_text,
        "work_format": vacancy.work_format,
        "employment": vacancy.employment,
        "experience": vacancy.experience_required,
        "source": vacancy.source,
    }
    return json.dumps(data, ensure_ascii=False)


def compute_fit_match(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
) -> dict:
    skills = get_vacancy_skills(session, vacancy.id)
    result = fit_from_profile_model(profile, vacancy, skills)
    data = fit_to_match_dict(result)
    upsert_match(session, vacancy.id, profile.id, MATCH_LEVEL, data)
    return data


def batch_fit_match(
    session: Session,
    profile_id: int | None = None,
    limit: int = 50,
    priority_vacancy_ids: list[int] | None = None,
) -> tuple[int, list[str]]:
    profile = session.get(CandidateProfile, profile_id) if profile_id else get_active_profile(session)
    if not profile:
        return 0, ["Профиль кандидата не найден. Загрузите резюме."]

    if not profile.resume_raw and not profile.skills_json:
        return 0, ["Профиль пуст — загрузите резюме для расчёта соответствия."]

    vacancies = list_for_matching(
        session,
        profile.id,
        match_level=MATCH_LEVEL,
        limit=limit,
        priority_vacancy_ids=priority_vacancy_ids,
    )
    if not vacancies:
        return 0, []

    matched = 0
    errors: list[str] = []

    for v in vacancies:
        try:
            data = compute_fit_match(session, profile, v)
            matched += 1
            logger.info("fit #%s [%s%%] %s", v.id, data["match_score"], v.title[:45])
        except Exception as exc:
            errors.append(f"#{v.id}: {exc}")
            logger.warning("fit #%s failed: %s", v.id, exc)

    return matched, errors
