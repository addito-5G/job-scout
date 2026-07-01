from __future__ import annotations

import json

from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from db.models import Vacancy


def vacancy_stats(session: Session) -> dict:
    row = session.execute(
        select(
            func.count().label("total"),
            func.sum(case((Vacancy.rule_score >= 40, 1), else_=0)).label("fit"),
            func.sum(case(((Vacancy.rule_score < 40) & (Vacancy.rule_score > 0), 1), else_=0)).label("maybe"),
            func.sum(case((Vacancy.rule_score == 0, 1), else_=0)).label("not_fit"),
            func.avg(Vacancy.rule_score).label("avg_score"),
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
    ).one()
    return {
        "total": row.total or 0,
        "fit": row.fit or 0,
        "maybe": row.maybe or 0,
        "not_fit": row.not_fit or 0,
        "avg_score": float(row.avg_score or 0),
        "enriched": row.enriched or 0,
    }


def save_daily_metrics(session: Session, metric_date: str, payload: dict) -> None:
    summary = payload.get("summary", payload)
    session.execute(
        text(
            """
            INSERT INTO daily_metrics (
                metric_date, total_vacancies, fit_count, not_fit_count,
                avg_score, median_salary, top_skills, payload
            ) VALUES (:metric_date, :total, :fit, :not_fit, :avg_score, :median_salary, :top_skills, :payload)
            ON CONFLICT(metric_date) DO UPDATE SET
                total_vacancies = excluded.total_vacancies,
                fit_count = excluded.fit_count,
                not_fit_count = excluded.not_fit_count,
                avg_score = excluded.avg_score,
                median_salary = excluded.median_salary,
                top_skills = excluded.top_skills,
                payload = excluded.payload,
                created_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "metric_date": metric_date,
            "total": summary.get("total", payload.get("total_vacancies", 0)),
            "fit": summary.get("fit", payload.get("fit_count", 0)),
            "not_fit": summary.get("not_fit", payload.get("not_fit_count", 0)),
            "avg_score": summary.get("avg_score", payload.get("avg_score")),
            "median_salary": summary.get("median_salary", payload.get("median_salary")),
            "top_skills": json.dumps(payload.get("top_skills", []), ensure_ascii=False),
            "payload": json.dumps(payload, ensure_ascii=False),
        },
    )
    session.commit()


def get_daily_metrics(session: Session, limit: int = 30) -> list[dict]:
    rows = session.execute(
        text(
            """
            SELECT metric_date, total_vacancies, fit_count, not_fit_count,
                   avg_score, median_salary, payload
            FROM daily_metrics
            ORDER BY metric_date DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings()
    return [dict(r) for r in rows]
