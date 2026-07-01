from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from db.models import Company, Skill, Vacancy, VacancyMatch, VacancySkill
from db.normalize import experience_label, work_format_label
from services.profile_filter_service import vacancy_scope_condition
from services.vacancy_service import count_new_vacancies


def _scope(profile_role: str | None) -> list:
    cond = [Vacancy.is_active.is_(True)]
    scope = vacancy_scope_condition(profile_role)
    if scope is not None:
        cond.append(scope)
    return cond


def get_metrics(
    session: Session,
    profile_id: int | None,
    *,
    profile_role: str | None = None,
) -> dict:
    scope = _scope(profile_role)
    total = session.execute(select(func.count()).select_from(Vacancy).where(*scope)).scalar_one()
    new_7d = count_new_vacancies(session, 7)
    new_30d = count_new_vacancies(session, 30)

    salaries = [
        mid
        for mid in (
            _salary_mid(v)
            for v in session.execute(select(Vacancy).where(*scope)).scalars()
        )
        if mid
    ]
    median_salary = sorted(salaries)[len(salaries) // 2] if salaries else None

    avg_match = None
    if profile_id:
        avg_match = session.execute(
            select(func.avg(VacancyMatch.match_score)).where(
                VacancyMatch.profile_id == profile_id,
                VacancyMatch.match_level == "fast",
            )
        ).scalar_one()
        if avg_match is not None:
            avg_match = round(float(avg_match), 1)

    return {
        "total": total,
        "new_7d": new_7d,
        "new_30d": new_30d,
        "median_salary": median_salary,
        "avg_match_score": avg_match,
        "with_salary": len(salaries),
    }


def _salary_mid(v: Vacancy) -> int | None:
    if v.salary_from and v.salary_to:
        return (v.salary_from + v.salary_to) // 2
    return v.salary_from or v.salary_to


def work_format_distribution(
    session: Session,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Vacancy.work_format, func.count())
        .where(*_scope(profile_role))
        .group_by(Vacancy.work_format)
        .order_by(func.count().desc())
    ).all()
    return [(work_format_label(r[0]) if r[0] else "не указан", r[1]) for r in rows]


def top_skills(
    session: Session,
    limit: int = 10,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    query = (
        select(Skill.name, func.count())
        .join(VacancySkill, VacancySkill.skill_id == Skill.id)
        .join(Vacancy, Vacancy.id == VacancySkill.vacancy_id)
        .where(*_scope(profile_role))
        .group_by(Skill.name)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = session.execute(query).all()
    return [(r[0], r[1]) for r in rows]


def vacancy_timeline(
    session: Session,
    days: int = 30,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    since = datetime.utcnow() - timedelta(days=days)
    rows = session.execute(
        select(Vacancy.published_at, Vacancy.scraped_at).where(
            or_(Vacancy.published_at >= since, Vacancy.scraped_at >= since),
            *_scope(profile_role),
        )
    ).all()
    counter: Counter = Counter()
    for pub, scraped in rows:
        dt = pub or scraped
        if dt:
            counter[dt.date().isoformat()] += 1
    return [(d, counter[d]) for d in sorted(counter.keys())]


def source_distribution(
    session: Session,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Vacancy.source, func.count())
        .where(*_scope(profile_role))
        .group_by(Vacancy.source)
        .order_by(func.count().desc())
    ).all()
    labels = {"hh": "HeadHunter", "habr": "Habr", "geekjob": "Geekjob"}
    return [(labels.get(r[0], r[0]), int(r[1])) for r in rows]


def top_companies(
    session: Session,
    limit: int = 8,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Company.name, func.count())
        .join(Vacancy, Vacancy.company_id == Company.id)
        .where(*_scope(profile_role))
        .group_by(Company.name)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return [(r[0], int(r[1])) for r in rows if r[0]]


def experience_distribution(
    session: Session,
    *,
    profile_role: str | None = None,
) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Vacancy.experience_required, func.count())
        .where(*_scope(profile_role), Vacancy.experience_required.isnot(None))
        .group_by(Vacancy.experience_required)
    ).all()
    counter: Counter[str] = Counter()
    for raw, count in rows:
        if raw:
            counter[experience_label(raw)] += int(count)
    return counter.most_common(8)


def match_score_buckets(
    session: Session,
    profile_id: int | None,
    *,
    profile_role: str | None = None,
) -> dict[str, int]:
    if not profile_id:
        return {}
    query = (
        select(VacancyMatch.match_score)
        .join(Vacancy, Vacancy.id == VacancyMatch.vacancy_id)
        .where(
            VacancyMatch.profile_id == profile_id,
            VacancyMatch.match_level == "fast",
        )
    )
    scope = vacancy_scope_condition(profile_role)
    if scope is not None:
        query = query.where(scope)
    rows = session.execute(query).scalars().all()
    buckets = {"0–39%": 0, "40–59%": 0, "60–79%": 0, "80–100%": 0}
    for score in rows:
        s = float(score or 0)
        if s < 40:
            buckets["0–39%"] += 1
        elif s < 60:
            buckets["40–59%"] += 1
        elif s < 80:
            buckets["60–79%"] += 1
        else:
            buckets["80–100%"] += 1
    return buckets
