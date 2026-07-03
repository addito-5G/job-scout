from __future__ import annotations

import json
import re

from db.models import CandidateProfile, VacancyMatch

_ANALYST_TOOL_MARKERS = (
    "sql",
    "python",
    "pandas",
    "clickhouse",
    "click house",
    "datalens",
    "pyspark",
    "airflow",
    "tableau",
    "power bi",
    "excel",
    "spark",
)

_PM_MARKERS = (
    "roadmap",
    "backlog",
    "custdev",
    "jtbd",
    "discovery",
    "rice",
    "ice",
    "stakeholder",
    "gtm",
    "plg",
    "okr",
    "scrum",
    "agile",
    "hypothesis",
    "приоритиз",
    "запуск",
    "mvp",
    "nrp",
    "unit",
    "p&l",
    "метрик",
    "retention",
    "e-commerce",
    "e-com",
    "ecom",
    "маркетплейс",
    "marketplace",
    "b2b",
    "saas",
    "crm",
    "bitrix",
    "продукт",
    "product",
    "команд",
    "монетиз",
    "adoption",
    "проникновен",
    "выручк",
    "gmv",
)


def first_name_from(full_name: str | None) -> str:
    if not full_name:
        return "кандидат"
    return full_name.strip().split()[0]


def _loads(raw: str | None, default: list | dict | None = None):
    try:
        return json.loads(raw or ("[]" if isinstance(default, list) else "{}"))
    except json.JSONDecodeError:
        return default if default is not None else []


def _is_analyst_tool(skill: str) -> bool:
    low = skill.lower()
    return any(marker in low for marker in _ANALYST_TOOL_MARKERS)


def _is_pm_relevant(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in _PM_MARKERS)


def _strength_for_pm_letter(strength: str) -> bool:
    low = strength.lower()
    if re.match(r"более\s+\d+\s+лет", low):
        return False
    if "без выделенного аналитика" in low:
        return False
    if re.search(r"\b(sql|python|clickhouse|datalens)\b", low) and not _is_pm_relevant(low):
        return False
    return _is_pm_relevant(low) or "запуск" in low or "масштабир" in low or "nrp" in low


def role_title_for_letter(profile: CandidateProfile, target_role: str) -> str:
    if target_role == "product_manager":
        return "Product Manager"
    if target_role == "product_analyst":
        return "продуктовый аналитик"
    title = (profile.title or "").strip()
    if title:
        return title.split("/")[0].strip()
    return "специалист"


def profile_for_cover_letter_json(profile: CandidateProfile, *, target_role: str) -> str:
    skills = _loads(profile.skills_json, [])
    pm_skills: list[str] = []
    analyst_tools: list[str] = []
    for skill in skills:
        if _is_analyst_tool(skill):
            analyst_tools.append(skill)
        else:
            pm_skills.append(skill)

    strengths = _loads(profile.strengths_json, [])
    pm_achievements = [s for s in strengths if _strength_for_pm_letter(s)]

    domains = _loads(profile.domains_json, [])

    data = {
        "first_name": first_name_from(profile.full_name),
        "role_title": role_title_for_letter(profile, target_role),
        "domains": domains,
        "pm_skills": pm_skills,
        "pm_achievements": pm_achievements,
        "analyst_tools_supplement": analyst_tools,
        "experience_years": profile.experience_years,
    }
    if target_role == "product_manager":
        data["note"] = (
            "Для письма используй pm_achievements и pm_skills как основу. "
            "analyst_tools_supplement — только в блоке доп. навыков, 1 предложение."
        )
    return json.dumps(data, ensure_ascii=False)


def match_context_for_cover_letter(match: VacancyMatch | None) -> str:
    if not match:
        return "{}"
    try:
        matched = json.loads(match.matched_skills_json or "[]")
        missing = json.loads(match.missing_skills_json or "[]")
        strengths = json.loads(match.strengths_for_vacancy_json or "[]")
    except json.JSONDecodeError:
        matched, missing, strengths = [], [], []

    pm_matched = [s for s in matched if not _is_analyst_tool(s) or _is_pm_relevant(s)]
    analyst_matched = [s for s in matched if _is_analyst_tool(s)]

    return json.dumps(
        {
            "pm_matched_skills": pm_matched,
            "analyst_matched_skills": analyst_matched,
            "missing_skills": missing,
            "strengths_for_this_vacancy": strengths,
            "fit_summary": match.recommendation_reason or match.ai_analysis or "",
        },
        ensure_ascii=False,
    )
