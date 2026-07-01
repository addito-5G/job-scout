from __future__ import annotations

import json
import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ai import AIRouter
from ai.schemas.match import VacancyMatchSchema
from db.models import CandidateProfile, Vacancy
from db.repositories.match_repo import upsert_match
from db.repositories.vacancy_repo import get_vacancy_skills, list_for_matching
from services.profile_service import get_latest_profile

logger = logging.getLogger(__name__)


def profile_to_json(profile: CandidateProfile) -> str:
    def loads(raw):
        try:
            return json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []

    data = {
        "full_name": profile.full_name,
        "title": profile.title,
        "experience_years": profile.experience_years,
        "skills": loads(profile.skills_json),
        "strengths": loads(profile.strengths_json),
        "weaknesses": loads(profile.weaknesses_json),
        "recommended_roles": loads(profile.recommended_roles_json),
        "ai_summary": profile.ai_summary,
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
    }
    return json.dumps(data, ensure_ascii=False)


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


def _parse_match_result(parsed: dict | None) -> dict:
    if not parsed:
        return {
            "match_score": 0,
            "match_summary": "Не удалось разобрать ответ AI",
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "skip",
        }
    try:
        schema = VacancyMatchSchema.model_validate(parsed)
        return schema.model_dump()
    except ValidationError:
        return {
            "match_score": int(parsed.get("match_score", 0)),
            "match_summary": parsed.get("match_summary", ""),
            "matched_skills": parsed.get("matched_skills", []),
            "missing_skills": parsed.get("missing_skills", []),
            "strengths": parsed.get("strengths", []),
            "risks": parsed.get("risks", []),
            "recommendation": parsed.get("recommendation", "skip"),
            "deep_analysis": parsed.get("deep_analysis", ""),
        }


def fast_match_vacancy(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    router: AIRouter | None = None,
) -> dict:
    router = router or AIRouter(session)
    payload = {
        "profile_id": profile.id,
        "vacancy_id": vacancy.id,
        "profile_json": profile_to_json(profile),
        "vacancy_json": vacancy_to_json(session, vacancy),
    }
    result = router.route("fast_match", payload, parse_json=True)
    data = _parse_match_result(result.parsed)
    upsert_match(session, vacancy.id, profile.id, "fast", data)
    return data


def deep_match_vacancy(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    router: AIRouter | None = None,
) -> dict:
    router = router or AIRouter(session)
    payload = {
        "profile_id": profile.id,
        "vacancy_id": vacancy.id,
        "profile_json": profile_to_json(profile),
        "vacancy_json": vacancy_to_json(session, vacancy),
    }
    result = router.route("match_vacancy_deep", payload, parse_json=True)
    data = _parse_match_result(result.parsed)
    upsert_match(session, vacancy.id, profile.id, "deep", data)
    return data


def batch_fast_match(
    session: Session,
    profile_id: int | None = None,
    limit: int = 30,
    min_score: int = 0,
) -> tuple[int, list[str]]:
    profile = session.get(CandidateProfile, profile_id) if profile_id else get_latest_profile(session)
    if not profile:
        return 0, ["Профиль кандидата не найден. Запустите scripts/setup.py"]

    vacancies = list_for_matching(
        session, profile.id, match_level="fast", limit=limit, min_score=min_score
    )
    if not vacancies:
        return 0, []

    router = AIRouter(session)
    matched = 0
    errors: list[str] = []

    for v in vacancies:
        try:
            data = fast_match_vacancy(session, profile, v, router=router)
            matched += 1
            logger.info("match #%s [%s%%] %s", v.id, data["match_score"], v.title[:45])
        except Exception as exc:
            errors.append(f"#{v.id}: {exc}")
            logger.warning("match #%s failed: %s", v.id, exc)

    return matched, errors
