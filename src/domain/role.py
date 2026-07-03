"""Единые константы и эвристики роли (PM / аналитик / general).

Два пути инференса намеренно разделены:

- ``infer_role_from_title`` — для фильтров, тегов вакансий, backfill; ``None`` если роль неизвестна.
- ``infer_target_role`` — для cover letter; всегда возвращает строку, включая ``general``.
"""

from __future__ import annotations

import re

ROLE_PRODUCT_ANALYST = "product_analyst"
ROLE_PRODUCT_MANAGER = "product_manager"
ROLE_GENERAL = "general"

# Ключевые слова для фильтрации профиля / вакансий (profile_filter_service).
ANALYST_TITLE_KW = (
    "аналитик",
    "analyst",
    "data analyst",
    "bi analyst",
    "продуктовый аналитик",
    "product analyst",
)
PM_TITLE_KW = (
    "product manager",
    "продакт",
    "product owner",
    "lead product",
    "head of product",
    "growth manager",
    "growth product",
)

DEFAULT_ROLE_LABELS = {
    ROLE_PRODUCT_ANALYST: "Продуктовый аналитик",
    ROLE_PRODUCT_MANAGER: "Product Manager",
}


def slug_role(title: str) -> str:
    """Стабильный ключ роли из названия должности."""
    normalized = re.sub(r"[^\w\s-]", "", title.lower().replace("ё", "е"))
    slug = re.sub(r"[\s-]+", "_", normalized).strip("_")
    return (slug[:64] if slug else ROLE_GENERAL)


def infer_role_from_title(title: str | None) -> str | None:
    """Роль из названия должности; для неизвестных — slug из title."""
    if not title:
        return None
    low = title.lower()
    if any(k in low for k in ANALYST_TITLE_KW):
        return ROLE_PRODUCT_ANALYST
    if any(k in low for k in PM_TITLE_KW):
        return ROLE_PRODUCT_MANAGER
    return slug_role(title)


def infer_target_role(vacancy_title: str) -> str:
    """Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)."""
    title = (vacancy_title or "").lower().replace("ё", "е")
    if any(
        k in title
        for k in (
            "product manager",
            "product owner",
            "продакт-менеджер",
            "продакт менеджер",
            "продуктовый менеджер",
            "менеджер продукта",
            "product lead",
            "head of product",
        )
    ):
        return ROLE_PRODUCT_MANAGER
    if any(
        k in title
        for k in (
            "product analyst",
            "продуктовый аналитик",
            "продакт-аналитик",
            "продакт аналитик",
            "product analytics",
        )
    ):
        return ROLE_PRODUCT_ANALYST
    if re.search(r"\bpo\b", title) or re.search(r"\bpm\b", title):
        return ROLE_PRODUCT_MANAGER
    return ROLE_GENERAL


def role_label(role: str) -> str:
    return DEFAULT_ROLE_LABELS.get(role, role.replace("_", " ").title())
