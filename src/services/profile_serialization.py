"""Единая сериализация профиля кандидата для AI и UI."""

from __future__ import annotations

import json

from db.models import CandidateProfile


def loads_json(raw: str | None, default: list | dict | None = None):
    """Безопасный json.loads с fallback."""
    if default is None:
        default = []
    try:
        return json.loads(raw or ("[]" if isinstance(default, list) else "{}"))
    except json.JSONDecodeError:
        return default


def to_match_json(profile: CandidateProfile) -> str:
    """JSON для fast/deep match (совпадает с прежним profile_to_json)."""
    data = {
        "full_name": profile.full_name,
        "title": profile.title,
        "experience_years": profile.experience_years,
        "skills": loads_json(profile.skills_json, []),
        "strengths": loads_json(profile.strengths_json, []),
        "weaknesses": loads_json(profile.weaknesses_json, []),
        "recommended_roles": loads_json(profile.recommended_roles_json, []),
        "ai_summary": profile.ai_summary,
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
    }
    return json.dumps(data, ensure_ascii=False)


def to_search_dict(profile: CandidateProfile) -> dict:
    """Словарь для suggest_filters и настроек поиска."""
    return {
        "full_name": profile.full_name,
        "title": profile.title,
        "experience_years": profile.experience_years,
        "skills": loads_json(profile.skills_json, []),
        "strengths": loads_json(profile.strengths_json, []),
        "weaknesses": loads_json(profile.weaknesses_json, []),
        "recommended_roles": loads_json(profile.recommended_roles_json, []),
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
        "salary_currency": profile.salary_currency,
        "ai_summary": profile.ai_summary,
    }


def to_cover_letter_json(profile: CandidateProfile, *, target_role: str) -> str:
    """Делегирует в cover_letter_context — формат v8 не меняется."""
    from services.cover_letter_context import profile_for_cover_letter_json

    return profile_for_cover_letter_json(profile, target_role=target_role)
