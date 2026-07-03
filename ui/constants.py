"""Подписи рекомендаций AI-match для UI."""

from __future__ import annotations

RECOMMENDATION_LABELS: dict[str, str] = {
    "apply": "✅ Откликаться",
    "skip": "⏭ Пропустить",
    "improve_resume": "📝 Усилить резюме",
    "consider": "🤔 Рассмотреть",
}

RECOMMENDATION_LABELS_SHORT: dict[str, str] = {
    "apply": "Откликаться",
    "skip": "Пропустить",
    "improve_resume": "Усилить резюме",
    "consider": "Рассмотреть",
}


def recommendation_label(recommendation: str | None, *, short: bool = False) -> str:
    rec = (recommendation or "").strip()
    if not rec:
        return "—"
    labels = RECOMMENDATION_LABELS_SHORT if short else RECOMMENDATION_LABELS
    return labels.get(rec, rec)
