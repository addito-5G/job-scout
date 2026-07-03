"""Преобразование VacancyMatch → dict и выбор лучшего AI-match."""

from __future__ import annotations

import json
from dataclasses import dataclass

from db.models import VacancyMatch


@dataclass(frozen=True)
class MatchSelection:
    """Выбранный AI-match: fast или deep (не путать с rule_score при скане)."""

    match: dict | None
    level: str | None

    @classmethod
    def pick(cls, fast_match: dict | None, deep_match: dict | None) -> MatchSelection:
        """Приоритет: deep с анализом → fast → пусто."""
        if match_has_analysis(deep_match):
            return cls(deep_match, "deep")
        if match_has_analysis(fast_match):
            return cls(fast_match, "fast")
        return cls(None, None)

    def as_tuple(self) -> tuple[dict | None, str | None]:
        return self.match, self.level


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

    return {
        "match_score": int(row.match_score or 0),
        "match_summary": row.recommendation_reason or (row.ai_analysis or "")[:500],
        "matched_skills": loads(row.matched_skills_json),
        "missing_skills": loads(row.missing_skills_json),
        "strengths": loads(row.strengths_for_vacancy_json),
        "risks": loads(row.risks_json),
        "recommendation": row.recommendation,
        "deep_analysis": row.ai_analysis,
        "cover_letter_draft": row.cover_letter_draft,
    }


def match_has_analysis(match: dict | None) -> bool:
    """Есть ли в записи реальный AI-анализ (не пустая заглушка под письмо)."""
    if not match:
        return False
    if match.get("matched_skills") or match.get("missing_skills"):
        return True
    if (match.get("match_summary") or "").strip():
        return True
    if (match.get("deep_analysis") or "").strip():
        return True
    if match.get("strengths") or match.get("risks"):
        return True
    score = match.get("match_score") or 0
    return score > 0 and bool(match.get("recommendation"))


def pick_best_match(fast_match: dict | None, deep_match: dict | None) -> tuple[dict | None, str | None]:
    return MatchSelection.pick(fast_match, deep_match).as_tuple()


def cover_letter_from_rows(fast: VacancyMatch | None, deep: VacancyMatch | None) -> str | None:
    for row in (deep, fast):
        if row and row.cover_letter_draft:
            return row.cover_letter_draft
    return None
