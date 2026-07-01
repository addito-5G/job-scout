from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from db.models import Company, Skill, Vacancy, VacancySkill
from db.repositories.metrics_repo import get_daily_metrics, vacancy_stats

STACK_KEYWORDS = [
    "jira", "confluence", "figma", "sql", "python", "tableau", "power bi",
    "amplitude", "mixpanel", "google analytics", "notion", "miro",
    "api", "saas", "b2b", "fintech", "маркетплейс", "wildberries", "ozon",
]


def build_analytics(session: Session, criteria: dict | None = None) -> dict:
    criteria = criteria or {}
    min_score = criteria.get("thresholds", {}).get("min_score", 40)
    rows = list(
        session.execute(
            select(Vacancy).options(joinedload(Vacancy.company_rel))
        ).unique().scalars()
    )
    stats = vacancy_stats(session)

    skills_counter: Counter = Counter()
    company_counter: Counter = Counter()
    salaries: list[int] = []
    score_buckets = {"0": 0, "1-39": 0, "40-54": 0, "55-69": 0, "70+": 0}
    vacancies = []

    skill_rows = session.execute(
        select(Skill.name, func.count())
        .join(VacancySkill, VacancySkill.skill_id == Skill.id)
        .group_by(Skill.name)
    ).all()
    for name, cnt in skill_rows:
        skills_counter[name] = cnt

    for row in rows:
        score = row.rule_score or 0
        if score == 0:
            score_buckets["0"] += 1
        elif score < 40:
            score_buckets["1-39"] += 1
        elif score < 55:
            score_buckets["40-54"] += 1
        elif score < 70:
            score_buckets["55-69"] += 1
        else:
            score_buckets["70+"] += 1

        company_name = row.company_rel.name if row.company_rel else None
        if company_name:
            company_counter[company_name] += 1

        mid = _salary_mid(row)
        if mid:
            salaries.append(mid)

        vacancies.append({
            "id": row.id,
            "title": row.title,
            "company": company_name,
            "url": row.external_url,
            "score": score,
            "status": row.user_status,
            "salary": row.salary_text,
            "fit": score >= min_score,
            "enriched": bool(row.description_full),
        })

    history = []
    for m in get_daily_metrics(session, limit=30):
        history.append({
            "date": m["metric_date"],
            "total": m["total_vacancies"],
            "fit": m["fit_count"],
            "not_fit": m["not_fit_count"],
            "avg_score": m["avg_score"],
            "median_salary": m["median_salary"],
        })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total": stats["total"] or 0,
            "fit": stats["fit"] or 0,
            "maybe": stats["maybe"] or 0,
            "not_fit": stats["not_fit"] or 0,
            "avg_score": round(stats["avg_score"] or 0, 1),
            "enriched": stats["enriched"] or 0,
            "median_salary": median(salaries) if salaries else None,
            "with_salary": len(salaries),
            "min_score": min_score,
        },
        "score_distribution": score_buckets,
        "top_skills": skills_counter.most_common(20),
        "top_companies": company_counter.most_common(15),
        "history": list(reversed(history)),
        "vacancies": vacancies,
    }


def _salary_mid(row: Vacancy) -> int | None:
    if row.salary_from and row.salary_to:
        return (row.salary_from + row.salary_to) // 2
    return row.salary_from or row.salary_to


def snapshot_for_today(analytics: dict) -> dict:
    today = date.today().isoformat()
    s = analytics["summary"]
    return {
        "metric_date": today,
        "total_vacancies": s["total"],
        "fit_count": s["fit"],
        "not_fit_count": s["not_fit"] + s["maybe"],
        "avg_score": s["avg_score"],
        "median_salary": s["median_salary"],
        "top_skills": analytics["top_skills"][:10],
        **analytics,
    }
