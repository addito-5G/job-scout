from __future__ import annotations

import json
import re
from collections import Counter

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ai import AIRouter
from ai.ai_router import AIRouterError
from db.models import CandidateProfile, Company, Skill, Vacancy, VacancySkill
from db.normalize import experience_label, work_format_label
from services.dashboard_service import top_skills
from services.profile_filter_service import vacancy_profile_scope
from services.profile_service import get_active_profile
from services.profile_serialization import loads_json, to_search_dict


def _vacancy_base(session: Session, profile_id: int | None):
    cond = [Vacancy.is_active.is_(True)]
    scope = vacancy_profile_scope(profile_id)
    if scope is not None:
        cond.append(scope)
    return cond


def _salary_stats(session: Session, base: list) -> dict:
    rows = session.execute(
        select(Vacancy.salary_from, Vacancy.salary_to, Vacancy.salary_text).where(
            *base,
            or_(Vacancy.salary_from.isnot(None), Vacancy.salary_to.isnot(None), Vacancy.salary_text.isnot(None)),
        )
    ).all()
    mids: list[int] = []
    for lo, hi, text in rows:
        if lo and hi:
            mids.append((lo + hi) // 2)
        elif lo:
            mids.append(lo)
        elif hi:
            mids.append(hi)
    if not mids:
        return {}
    mids.sort()
    return {
        "median_rub": mids[len(mids) // 2],
        "min_rub": mids[0],
        "max_rub": mids[-1],
        "with_salary_count": len(mids),
    }


def _extract_requirement_lines(text: str, limit: int = 12) -> list[str]:
    lines: list[str] = []
    capture = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            capture = False
            continue
        lower = line.lower().rstrip(":")
        if lower in ("обязанности", "требования", "требуется", "мы ждём", "мы ждем", "задачи", "ожидания"):
            capture = True
            continue
        if capture and (line.startswith("-") or line.startswith("•") or line.startswith("*")):
            lines.append(line.lstrip("-•* ").strip()[:280])
            if len(lines) >= limit:
                break
            continue
        if len(line) < 12:
            continue
        if any(
            kw in lower
            for kw in (
                "требован",
                "обязанност",
                "ожида",
                "нужно",
                "необходим",
                "опыт",
                "навык",
                "знание",
                "умение",
                "будет плюсом",
                "мы ждём",
                "мы ждем",
                "вы будете",
                "задачи",
            )
        ):
            lines.append(line[:280])
        if len(lines) >= limit:
            break
    return lines


def collect_market_requirements(
    session: Session,
    *,
    profile_id: int | None = None,
    limit: int = 100,
    sample_vacancies: int = 20,
) -> dict:
    """Требования рынка из вакансий активного профиля резюме."""
    base = _vacancy_base(session, profile_id)
    vacancy_count = session.execute(
        select(func.count()).select_from(Vacancy).where(*base)
    ).scalar_one()

    skills = top_skills(session, limit=25, profile_id=profile_id)
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
    top_titles = list(dict.fromkeys(title_rows))[:25]

    title_words: Counter[str] = Counter()
    for title in title_rows:
        for word in title.lower().replace("/", " ").replace("-", " ").split():
            w = word.strip(".,()")
            if len(w) > 3:
                title_words[w] += 1
    frequent_title_terms = [w for w, _ in title_words.most_common(25)]

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

    vacancy_samples: list[dict] = []
    requirement_lines: list[str] = []
    sample_rows = session.execute(
        select(Vacancy, Company.name)
        .outerjoin(Company, Company.id == Vacancy.company_id)
        .where(*base)
        .order_by(Vacancy.published_at.desc().nullslast())
        .limit(sample_vacancies)
    ).all()

    for vac, company_name in sample_rows:
        body = (vac.description_full or vac.description_short or "").strip()
        excerpt = body[:1200] if body else ""
        req_lines = _extract_requirement_lines(body) if body else []
        requirement_lines.extend(req_lines)
        vacancy_samples.append(
            {
                "title": vac.title,
                "company": company_name or "—",
                "work_format": work_format_label(vac.work_format) if vac.work_format else None,
                "salary": vac.salary_text,
                "experience": experience_label(vac.experience_required) if vac.experience_required else None,
                "source": vac.source,
                "description_excerpt": excerpt,
                "requirement_lines": req_lines[:6],
            }
        )

    # dedupe requirement lines
    seen_req: set[str] = set()
    unique_requirements: list[str] = []
    for line in requirement_lines:
        key = line.lower()[:80]
        if key not in seen_req:
            seen_req.add(key)
            unique_requirements.append(line)
        if len(unique_requirements) >= 40:
            break

    return {
        "vacancy_count": int(vacancy_count),
        "top_skills": skill_names or linked_skills[:25],
        "linked_skills": linked_skills,
        "top_titles": top_titles,
        "experience_distribution": experience_distribution,
        "work_format_distribution": work_formats,
        "salary_stats": _salary_stats(session, base),
        "frequent_title_terms": frequent_title_terms,
        "common_requirements": unique_requirements,
        "vacancy_samples": vacancy_samples,
        "profile_id": profile_id,
    }


def _target_role(profile: CandidateProfile) -> str:
    roles = loads_json(profile.recommended_roles_json, [])
    if profile.title:
        return profile.title
    if roles:
        return str(roles[0])
    return profile.display_name or "специалист"


def compact_market_for_ai(market: dict) -> dict:
    """Сжатый срез рынка для AI (полный market — десятки KB, модель теряет резюме)."""
    highlights = []
    for item in market.get("vacancy_samples", [])[:6]:
        highlights.append(
            {
                "title": item.get("title"),
                "company": item.get("company"),
                "requirements": (item.get("requirement_lines") or [])[:5],
                "snippet": (item.get("description_excerpt") or "")[:400],
            }
        )
    return {
        "vacancy_count": market.get("vacancy_count", 0),
        "top_titles": market.get("top_titles", [])[:12],
        "top_skills": market.get("top_skills", [])[:20],
        "common_requirements": market.get("common_requirements", [])[:25],
        "frequent_title_terms": market.get("frequent_title_terms", [])[:15],
        "experience_distribution": market.get("experience_distribution"),
        "work_format_distribution": market.get("work_format_distribution"),
        "salary_stats": market.get("salary_stats"),
        "vacancy_highlights": highlights,
    }


_HALLUCINATION_MARKERS = (
    "компания a",
    "компания b",
    "компания c",
    "компания d",
    "иван петров",
    "предположим",
    "данные не указаны",
    "не указана явно",
)


def _parse_advice_result(result) -> dict:
    advice = result.parsed if result.parsed else {}
    if not isinstance(advice, dict):
        advice = {}
    if not advice.get("improved_resume_markdown") and result.content:
        extracted = _fallback_resume_from_text(result.content)
        if extracted:
            advice["improved_resume_markdown"] = extracted
    if not advice.get("summary") and result.content and not advice.get("improved_resume_markdown"):
        advice["summary"] = result.content[:500]
    return advice


_REQUIRED_SECTION_MARKERS = (
    "ключевые навыки",
    "профессиональные компетенции",
    "владение программами",
    "о себе",
)


def _validate_advice(advice: dict, profile: CandidateProfile) -> tuple[bool, str]:
    improved = (advice.get("improved_resume_markdown") or "").strip()
    if not improved:
        return False, "AI не вернул текст улучшенного резюме"

    lower = improved.lower()
    for marker in _HALLUCINATION_MARKERS:
        if marker in lower:
            return False, f"Обнаружены выдуманные данные: «{marker}»"

    for section in _REQUIRED_SECTION_MARKERS:
        if section not in lower:
            return False, f"В резюме нет обязательной секции «{section}»"

    full_name = (profile.full_name or "").strip()
    if full_name:
        parts = [p for p in full_name.split() if len(p) > 2]
        if parts:
            surname = parts[0].lower()
            if surname not in lower:
                return False, f"В резюме нет фамилии кандидата ({parts[0]})"

    return True, ""


def generate_resume_advice(
    session: Session,
    profile_id: int | None = None,
    *,
    use_cache: bool = False,
) -> dict:
    if profile_id is not None:
        profile = session.get(CandidateProfile, profile_id)
    else:
        profile = get_active_profile(session)
    if not profile:
        raise ValueError("Профиль не найден. Загрузите резюме.")
    if not profile.resume_raw:
        raise ValueError("Резюме пустое. Загрузите файл .md.")

    market_full = collect_market_requirements(session, profile_id=profile.id)
    if market_full["vacancy_count"] < 5:
        raise ValueError("Мало вакансий для этого профиля. Запустите парсинг или проверьте ключи поиска.")

    market = compact_market_for_ai(market_full)

    profile_data = to_search_dict(profile)
    profile_data["target_titles"] = loads_json(profile.recommended_roles_json, [])
    profile_data["display_name"] = profile.display_name
    if profile.title and profile.title not in profile_data["target_titles"]:
        profile_data["target_titles"] = [profile.title, *profile_data["target_titles"]]

    router = AIRouter(session)
    total_years = profile.experience_years
    if total_years is None and profile_data.get("experience_years"):
        total_years = profile_data.get("experience_years")

    candidate_name = profile.full_name or profile.display_name or "Кандидат"
    payload = {
        "profile_id": profile.id,
        "profile_label": profile.display_name,
        "candidate_full_name": candidate_name,
        "resume_text": profile.resume_raw,
        "profile_json": json.dumps(profile_data, ensure_ascii=False),
        "market_requirements_json": json.dumps(market, ensure_ascii=False),
        "vacancy_count": market_full["vacancy_count"],
        "target_role": _target_role(profile),
        "total_experience_years": total_years if total_years is not None else "посчитай из дат в RESUME",
    }

    attempts: list[tuple[bool, str | None]] = [
        (use_cache, None),
        (False, "yandex"),
        (False, "ollama"),
    ]
    last_error = "неизвестная ошибка"

    for cache_ok, force_provider in attempts:
        try:
            result = router.route(
                "improve_resume",
                payload,
                parse_json=True,
                use_cache=cache_ok,
                force_provider=force_provider,
            )
        except AIRouterError as exc:
            last_error = str(exc)
            continue

        advice = _parse_advice_result(result)
        valid, reason = _validate_advice(advice, profile)
        if valid:
            advice["profile_id"] = profile.id
            advice["profile_label"] = profile.display_name
            advice["candidate_name"] = candidate_name
            advice["market_snapshot"] = {
                "vacancy_count": market_full["vacancy_count"],
                "top_skills": market_full["top_skills"][:15],
                "top_titles": market_full["top_titles"][:10],
                "experience_distribution": market_full["experience_distribution"],
                "salary_stats": market_full.get("salary_stats"),
            }
            return advice
        last_error = reason

    raise ValueError(
        f"AI вернул некорректный результат ({last_error}). "
        "Попробуйте ещё раз или проверьте, что в резюме указано ФИО."
    )


def _fallback_resume_from_text(content: str) -> str:
    """Если модель вернула текст вне JSON — попытаться извлечь блок резюме."""
    match = re.search(r"improved_resume_markdown[\"']?\s*:\s*\"(.+?)\"\s*,", content, re.DOTALL)
    if match:
        return match.group(1).replace("\\n", "\n")
    return ""
