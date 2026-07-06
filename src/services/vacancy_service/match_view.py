"""Преобразование VacancyMatch → dict для UI."""

from __future__ import annotations

import json

from db.models import VacancyMatch

MATCH_LEVEL = "fit"
LEGACY_LEVELS = ("fit", "deep", "fast")


def match_to_dict(row: VacancyMatch | None) -> dict | None:
    if not row:
        return None

    def loads(raw: str | None) -> list:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    missing = loads(row.missing_skills_json)
    gaps = [f"Усилить в резюме и опыте: {item}" for item in missing[:6]]

    return {
        "match_score": int(row.match_score or 0),
        "match_summary": row.recommendation_reason or (row.ai_analysis or "")[:500],
        "matched_skills": loads(row.matched_skills_json),
        "missing_skills": missing,
        "gaps_to_improve": gaps,
        "strengths": loads(row.strengths_for_vacancy_json),
        "risks": loads(row.risks_json),
        "recommendation": row.recommendation,
        "cover_letter_draft": row.cover_letter_draft,
    }


def match_has_analysis(match: dict | None) -> bool:
    if not match:
        return False
    if match.get("matched_skills") or match.get("missing_skills"):
        return True
    if (match.get("match_summary") or "").strip():
        return True
    if match.get("strengths") or match.get("risks"):
        return True
    return (match.get("match_score") or 0) > 0


def pick_best_match(*matches: dict | None) -> dict | None:
    for match in matches:
        if match_has_analysis(match):
            return match
    return None


def cover_letter_from_rows(*rows: VacancyMatch | None) -> str | None:
    for row in rows:
        if row and row.cover_letter_draft:
            return row.cover_letter_draft
    return None
