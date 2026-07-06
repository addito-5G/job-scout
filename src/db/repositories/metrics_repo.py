from __future__ import annotations

import json
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from db.models import DailyMetrics, Vacancy, VacancyMatch
from db.repositories.vacancy_repo import count_new_vacancies


def vacancy_stats(session: Session) -> dict:
    fit_subq = (
        select(
            VacancyMatch.vacancy_id,
            func.max(VacancyMatch.match_score).label("best_score"),
        )
        .where(VacancyMatch.match_level.in_(("fit", "deep", "fast")))
        .group_by(VacancyMatch.vacancy_id)
        .subquery()
    )
    row = session.execute(
        select(
            func.count().label("total"),
            func.sum(case((fit_subq.c.best_score >= 50, 1), else_=0)).label("fit"),
            func.sum(
                case(
                    ((fit_subq.c.best_score < 50) & (fit_subq.c.best_score > 0), 1),
                    else_=0,
                )
            ).label("maybe"),
            func.sum(case((fit_subq.c.best_score.is_(None), 1), else_=0)).label("not_fit"),
            func.avg(fit_subq.c.best_score).label("avg_score"),
            func.sum(
                case(
                    (
                        (Vacancy.description_full.isnot(None)) & (Vacancy.description_full != ""),
                        1,
                    ),
                    else_=0,
                )
            ).label("enriched"),
        )
        .select_from(Vacancy)
        .outerjoin(fit_subq, fit_subq.c.vacancy_id == Vacancy.id)
        .where(Vacancy.is_active.is_(True))
    ).one()
    return {
        "total": row.total or 0,
        "fit": row.fit or 0,
        "maybe": row.maybe or 0,
        "not_fit": row.not_fit or 0,
        "avg_score": float(row.avg_score or 0),
        "enriched": row.enriched or 0,
    }


def _metrics_row_to_dict(row: DailyMetrics) -> dict:
    return {
        "metric_date": row.metric_date,
        "total_vacancies": row.total_vacancies,
        "fit_count": row.fit_count,
        "not_fit_count": row.not_fit_count,
        "avg_score": row.avg_match_score,
        "median_salary": row.median_salary_all,
        "payload": row.payload,
    }


def save_daily_metrics(session: Session, metric_date: str, payload: dict) -> None:
    summary = payload.get("summary", payload)
    top_skills = payload.get("top_skills", [])
    if top_skills and isinstance(top_skills[0], (list, tuple)):
        top_skills = top_skills[:10]

    row = session.execute(
        select(DailyMetrics).where(DailyMetrics.metric_date == metric_date)
    ).scalar_one_or_none()

    fields = {
        "metric_date": metric_date,
        "total_vacancies": int(summary.get("total", payload.get("total_vacancies", 0)) or 0),
        "new_7d": count_new_vacancies(session, 7),
        "new_30d": count_new_vacancies(session, 30),
        "fit_count": int(summary.get("fit", payload.get("fit_count", 0)) or 0),
        "not_fit_count": int(
            (summary.get("not_fit", 0) or 0) + (summary.get("maybe", 0) or 0)
            or payload.get("not_fit_count", 0)
            or 0
        ),
        "avg_match_score": summary.get("avg_score", payload.get("avg_score")),
        "median_salary_all": summary.get("median_salary", payload.get("median_salary")),
        "median_salary_fit": payload.get("median_salary_fit"),
        "top_skills": json.dumps(top_skills, ensure_ascii=False),
        "payload": json.dumps(payload, ensure_ascii=False),
    }

    if row:
        for key, value in fields.items():
            if key != "metric_date":
                setattr(row, key, value)
    else:
        session.add(DailyMetrics(**fields))
    session.commit()


def get_daily_metrics(session: Session, limit: int = 30) -> list[dict]:
    rows = session.execute(
        select(DailyMetrics).order_by(DailyMetrics.metric_date.desc()).limit(limit)
    ).scalars().all()
    return [_metrics_row_to_dict(row) for row in rows]
