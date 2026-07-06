"""Тесты resume advice / market collection."""

from __future__ import annotations

import json

from db.models import CandidateProfile
from services.resume_advice_service import (
    _extract_requirement_lines,
    _validate_advice,
    compact_market_for_ai,
)


def test_extract_requirement_lines_finds_bullets():
    text = """
    Обязанности:
    - Вести переговоры с B2B-клиентами
    - Готовить отчёты

    Требования:
    - Опыт в продажах от 3 лет
    - Знание CRM
    """
    lines = _extract_requirement_lines(text)
    assert any("переговор" in ln.lower() for ln in lines)
    assert any("crm" in ln.lower() for ln in lines)


def test_compact_market_fits_ai_context():
    huge = {
        "vacancy_count": 50,
        "top_titles": ["PM"] * 30,
        "top_skills": ["sales"] * 30,
        "common_requirements": ["req"] * 40,
        "vacancy_samples": [
            {
                "title": "Sales",
                "company": "X",
                "requirement_lines": ["a"] * 10,
                "description_excerpt": "x" * 2000,
            }
        ]
        * 20,
    }
    compact = compact_market_for_ai(huge)
    assert len(json.dumps(compact, ensure_ascii=False)) < 12_000


def test_validate_rejects_hallucinated_name():
    profile = CandidateProfile(display_name="Nataly", full_name="Накимова Наталья")
    ok, _ = _validate_advice(
        {"improved_resume_markdown": "## Иван Петров\nМенеджер"},
        profile,
    )
    assert ok is False


def test_validate_accepts_correct_surname():
    profile = CandidateProfile(display_name="Nataly", full_name="Накимова Наталья")
    ok, _ = _validate_advice(
        {
            "improved_resume_markdown": (
                "## Накимова Наталья\n"
                "**Ключевые навыки:** продажи\n"
                "**Профессиональные компетенции:** B2B\n"
                "**Владение программами:** 1С\n"
                "**О себе:** менеджер"
            )
        },
        profile,
    )
    assert ok is True


def test_validate_rejects_missing_sections():
    profile = CandidateProfile(display_name="Nataly", full_name="Накимова Наталья")
    ok, reason = _validate_advice(
        {"improved_resume_markdown": "## Накимова Наталья\nМенеджер по продажам"},
        profile,
    )
    assert ok is False
    assert "секции" in reason.lower()
