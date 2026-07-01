from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import VacancyMatch


def upsert_match(
    session: Session,
    vacancy_id: int,
    profile_id: int,
    match_level: str,
    data: dict,
) -> VacancyMatch:
    row = session.execute(
        select(VacancyMatch).where(
            VacancyMatch.vacancy_id == vacancy_id,
            VacancyMatch.profile_id == profile_id,
            VacancyMatch.match_level == match_level,
        )
    ).scalar_one_or_none()

    fields = {
        "match_score": float(data.get("match_score", 0)),
        "matched_skills_json": json.dumps(data.get("matched_skills", []), ensure_ascii=False),
        "missing_skills_json": json.dumps(data.get("missing_skills", []), ensure_ascii=False),
        "strengths_for_vacancy_json": json.dumps(data.get("strengths", []), ensure_ascii=False),
        "risks_json": json.dumps(data.get("risks", []), ensure_ascii=False),
        "recommendation": data.get("recommendation"),
        "recommendation_reason": data.get("match_summary") or data.get("recommendation_reason"),
        "ai_analysis": data.get("deep_analysis") or data.get("match_summary", ""),
        "analyzed_at": datetime.utcnow(),
    }

    if row:
        for k, v in fields.items():
            setattr(row, k, v)
    else:
        row = VacancyMatch(
            vacancy_id=vacancy_id,
            profile_id=profile_id,
            match_level=match_level,
            **fields,
        )
        session.add(row)

    session.commit()
    session.refresh(row)
    return row


def get_match(
    session: Session,
    vacancy_id: int,
    profile_id: int,
    match_level: str = "fast",
) -> VacancyMatch | None:
    return session.execute(
        select(VacancyMatch).where(
            VacancyMatch.vacancy_id == vacancy_id,
            VacancyMatch.profile_id == profile_id,
            VacancyMatch.match_level == match_level,
        )
    ).scalar_one_or_none()
