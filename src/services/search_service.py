from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai import AIRouter
from db.models import CandidateProfile, SearchSettings
from services.profile_serialization import loads_json as _loads, to_search_dict as _profile_to_dict


def _defaults_from_profile(profile: CandidateProfile) -> dict:
    roles = _loads(profile.recommended_roles_json, [])
    if not roles and profile.title:
        roles = [profile.title]

    return {
        "desired_titles": roles[:3],
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
        "salary_currency": profile.salary_currency or "RUR",
        "regions": ["Москва"],
        "work_formats": ["remote", "hybrid"],
        "employment_types": ["full"],
        "keywords_include": ["product manager", "продакт"],
        "keywords_exclude": ["junior", "intern", "стажёр"],
        "required_skills": [],
        "experience_filter": "3+",
    }


def build_search_draft(
    session: Session,
    profile_id: int,
    *,
    use_ai: bool = True,
) -> dict:
    """Подобрать ключи для парсинга без сохранения в БД."""
    profile = session.get(CandidateProfile, profile_id)
    if not profile:
        raise ValueError(f"Profile #{profile_id} not found")

    data = _defaults_from_profile(profile)

    if use_ai:
        router = AIRouter(session)
        try:
            result = router.route(
                "suggest_filters",
                {"profile_json": json.dumps(_profile_to_dict(profile), ensure_ascii=False)},
                parse_json=True,
            )
            if result.parsed:
                data.update({k: v for k, v in result.parsed.items() if v not in (None, "", [])})
        except Exception:
            pass

    return data


def save_search_settings(session: Session, profile_id: int, data: dict) -> SearchSettings:
    """Сохранить пользовательские настройки поиска."""
    for old in session.execute(
        select(SearchSettings).where(
            SearchSettings.profile_id == profile_id,
            SearchSettings.is_active.is_(True),
        )
    ).scalars():
        old.is_active = False

    titles = [t.strip() for t in data.get("desired_titles", []) if t and str(t).strip()][:5]
    include = [k.strip() for k in data.get("keywords_include", []) if k and str(k).strip()]
    exclude = [k.strip() for k in data.get("keywords_exclude", []) if k and str(k).strip()]

    profile = session.get(CandidateProfile, profile_id)
    profile_label = profile.title if profile and profile.title else (titles[0] if titles else None)

    normalized = {
        **data,
        "desired_titles": titles,
        "keywords_include": include,
        "keywords_exclude": exclude,
    }

    queries = settings_to_queries_from_data(normalized)
    habr_queries = settings_to_habr_queries_from_data(normalized)
    settings = SearchSettings(
        profile_id=profile_id,
        desired_titles_json=json.dumps(titles, ensure_ascii=False),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_currency=data.get("salary_currency", "RUR"),
        locations_json=json.dumps(data.get("regions", []), ensure_ascii=False),
        work_formats_json=json.dumps(data.get("work_formats", []), ensure_ascii=False),
        employment_types_json=json.dumps(data.get("employment_types", []), ensure_ascii=False),
        keywords_include_json=json.dumps(include, ensure_ascii=False),
        keywords_exclude_json=json.dumps(exclude, ensure_ascii=False),
        required_skills_json=json.dumps(data.get("required_skills", []), ensure_ascii=False),
        experience_filter=data.get("experience_filter"),
        hh_queries_json=json.dumps(queries, ensure_ascii=False),
        habr_queries_json=json.dumps(habr_queries, ensure_ascii=False),
        geekjob_queries_json=json.dumps(habr_queries, ensure_ascii=False),
        profile_label=profile_label,
        is_active=True,
    )
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def search_settings_to_data(settings: SearchSettings) -> dict:
    return {
        "desired_titles": _loads(settings.desired_titles_json, []),
        "salary_min": settings.salary_min,
        "salary_max": settings.salary_max,
        "salary_currency": settings.salary_currency or "RUR",
        "regions": _loads(settings.locations_json, []),
        "work_formats": _loads(settings.work_formats_json, []),
        "employment_types": _loads(settings.employment_types_json, []),
        "keywords_include": _loads(settings.keywords_include_json, []),
        "keywords_exclude": _loads(settings.keywords_exclude_json, []),
        "required_skills": _loads(settings.required_skills_json, []),
        "experience_filter": settings.experience_filter,
    }


def suggest_search_settings(
    session: Session,
    profile_id: int,
    *,
    use_ai: bool = True,
) -> SearchSettings:
    data = build_search_draft(session, profile_id, use_ai=use_ai)
    return save_search_settings(session, profile_id, data)


def get_active_search_settings(session: Session, profile_id: int) -> SearchSettings | None:
    return session.execute(
        select(SearchSettings).where(
            SearchSettings.profile_id == profile_id,
            SearchSettings.is_active.is_(True),
        )
    ).scalar_one_or_none()


def settings_to_queries_from_data(data: dict) -> list[dict]:
    titles = data.get("desired_titles") or ["product manager"]
    queries = []
    for title in titles[:3]:
        q = {"text": title, "area": 1, "search_field": "name"}
        formats = data.get("work_formats") or []
        if "remote" in formats:
            q["schedule"] = "remote"
        queries.append(q)
    return queries


def settings_to_habr_queries_from_data(data: dict) -> list[str]:
    titles = data.get("desired_titles") or []
    keywords = data.get("keywords_include") or []
    seen: set[str] = set()
    queries: list[str] = []
    for item in [*titles[:3], *keywords[:5]]:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            queries.append(item.strip())
    return queries or ["product manager", "продакт"]


def settings_to_queries(settings: SearchSettings) -> list[dict]:
    cached = _loads(settings.hh_queries_json, None)
    if cached:
        return cached
    return settings_to_queries_from_data({
        "desired_titles": _loads(settings.desired_titles_json, []),
        "work_formats": _loads(settings.work_formats_json, []),
    })


def settings_to_habr_queries(settings: SearchSettings) -> list[str]:
    cached = _loads(settings.habr_queries_json, None)
    if cached:
        return cached
    return settings_to_habr_queries_from_data({
        "desired_titles": _loads(settings.desired_titles_json, []),
        "keywords_include": _loads(settings.keywords_include_json, []),
    })
