from __future__ import annotations

import re
from datetime import datetime, timezone

from models import Vacancy


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def score_vacancy(v: Vacancy, criteria: dict) -> Vacancy:
    text = _normalize(v.scoring_text())
    score = 0
    reasons: list[str] = []

    must = criteria.get("must_match", [])
    if not any(k in text for k in must):
        v.score = 0
        v.score_reasons = ["нет ключевых слов product/продакт"]
        return v

    score += 30
    reasons.append("роль PM/product (+30)")

    for kw in criteria.get("boost", []):
        if kw in text:
            score += 8
            reasons.append(f"{kw} (+8)")

    for kw in criteria.get("penalty", []):
        if kw in text:
            score -= 15
            reasons.append(f"{kw} (-15)")

    for loc in criteria.get("locations", []):
        if loc in text:
            score += 5
            reasons.append(f"локация {loc} (+5)")
            break

    if v.full_description:
        score += 5
        reasons.append("полное описание (+5)")

    if v.skills:
        score += min(10, len(v.skills) * 2)
        reasons.append(f"навыки {len(v.skills)} (+{min(10, len(v.skills) * 2)})")

    if v.published_at:
        age = (datetime.now(timezone.utc) - v.published_at.astimezone(timezone.utc)).days
        max_age = criteria.get("thresholds", {}).get("max_age_days", 14)
        if age > max_age:
            score -= 20
            reasons.append(f"старше {max_age} дн. (-20)")

    v.score = max(0, min(100, score))
    v.score_reasons = reasons
    return v
