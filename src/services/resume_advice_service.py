from __future__ import annotations

import json
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai import AIRouter
from ai.ai_router import AIRouterError
from db.models import CandidateProfile, Skill, Vacancy, VacancySkill
from db.normalize import experience_label, work_format_label
from services.dashboard_service import top_skills
from services.profile_filter_service import vacancy_scope_condition
from services.profile_service import get_latest_profile
from services.profile_serialization import loads_json, to_search_dict


def _vacancy_base(session: Session, profile_role: str | None):
    cond = [Vacancy.is_active.is_(True)]
    scope = vacancy_scope_condition(profile_role)
    if scope is not None:
        cond.append(scope)
    return cond


def collect_market_requirements(
    session: Session,
    *,
    profile_role: str | None = None,
    limit: int = 100,
) -> dict:
    """Требования рынка из вакансий выбранного профиля поиска."""
    base = _vacancy_base(session, profile_role)
    vacancy_count = session.execute(
        select(func.count()).select_from(Vacancy).where(*base)
    ).scalar_one()

    skills = top_skills(session, limit=25, profile_role=profile_role)
    skill_names = [name for name, _ in skills]

    exp_rows = session.execute(
        select(Vacancy.experience_required, func.count())
        .where(*base, Vacancy.experience_required.isnot(None))
        .group_by(Vacancy.experience_required)
    ).all()
    exp_counter: Counter[str] = Counter()
    for raw, count in exp_rows:
        if raw:
            exp_counter[experience_label(raw)] += int(count)
    experience_distribution = dict(exp_counter.most_common(8))

    format_rows = session.execute(
        select(Vacancy.work_format, func.count())
        .where(*base, Vacancy.work_format.isnot(None))
        .group_by(Vacancy.work_format)
    ).all()
    format_counter: Counter[str] = Counter()
    for raw, count in format_rows:
        if raw:
            format_counter[work_format_label(raw)] += int(count)
    work_formats = dict(format_counter)

    title_rows = session.execute(
        select(Vacancy.title)
        .where(*base)
        .order_by(Vacancy.published_at.desc().nullslast())
        .limit(limit)
    ).scalars().all()
    title_words: Counter[str] = Counter()
    for title in title_rows:
        for word in title.lower().replace("/", " ").replace("-", " ").split():
            w = word.strip(".,()")
            if len(w) > 3:
                title_words[w] += 1
    frequent_title_terms = [w for w, _ in title_words.most_common(20)]

    skill_query = (
        select(Skill.name, func.count())
        .join(VacancySkill, VacancySkill.skill_id == Skill.id)
        .join(Vacancy, Vacancy.id == VacancySkill.vacancy_id)
        .where(*base)
        .group_by(Skill.name)
        .order_by(func.count().desc())
        .limit(30)
    )
    linked_skills = [row[0] for row in session.execute(skill_query).all()]

    sample_snippets: list[str] = []
    desc_rows = session.execute(
        select(Vacancy.description_full, Vacancy.description_short)
        .where(*base)
        .order_by(Vacancy.rule_score.desc(), Vacancy.published_at.desc().nullslast())
        .limit(15)
    ).all()
    for full, short in desc_rows:
        text = (full or short or "").strip()
        if len(text) > 80:
            sample_snippets.append(text[:400])

    return {
        "vacancy_count": int(vacancy_count),
        "top_skills": skill_names or linked_skills[:25],
        "linked_skills": linked_skills,
        "experience_distribution": experience_distribution,
        "work_format_distribution": work_formats,
        "frequent_title_terms": frequent_title_terms,
        "sample_requirement_snippets": sample_snippets[:10],
        "profile_role": profile_role,
    }


def generate_resume_advice(
    session: Session,
    profile_id: int | None = None,
    *,
    profile_role: str | None = None,
) -> dict:
    if profile_id is not None:
        profile = session.get(CandidateProfile, profile_id)
    else:
        profile = get_latest_profile(session)
    if not profile:
        raise ValueError("Профиль не найден. Загрузите резюме.")
    if not profile.resume_raw:
        raise ValueError("Резюме пустое. Загрузите файл .md.")

    market = collect_market_requirements(session, profile_role=profile_role)
    if market["vacancy_count"] < 5:
        raise ValueError("Мало вакансий для выбранного профиля. Запустите парсинг или смените фильтр.")

    profile_data = to_search_dict(profile)
    profile_data["target_titles"] = loads_json(profile.recommended_roles_json, [])
    if profile.title and profile.title not in profile_data["target_titles"]:
        profile_data["target_titles"] = [profile.title, *profile_data["target_titles"]]

    router = AIRouter(session)
    try:
        result = router.route(
            "improve_resume",
            {
                "resume_text": profile.resume_raw,
                "profile_json": json.dumps(profile_data, ensure_ascii=False),
                "market_requirements_json": json.dumps(market, ensure_ascii=False),
                "vacancy_count": market["vacancy_count"],
            },
            parse_json=True,
        )
    except AIRouterError as exc:
        raise ValueError(f"AI недоступен: {exc}") from exc

    advice = result.parsed or {"summary": result.content}
    advice["market_snapshot"] = {
        "vacancy_count": market["vacancy_count"],
        "top_skills": market["top_skills"][:15],
        "experience_distribution": market["experience_distribution"],
    }
    return advice
