"""Тесты vacancy fit advice."""

from __future__ import annotations

from services.vacancy_fit_advice_service import _normalize_advice, _validate_advice


def test_validate_advice_requires_verdict_and_items():
    ok, _ = _validate_advice({})
    assert not ok

    ok, _ = _validate_advice(
        {
            "verdict": "Коротко",
            "resume_additions": [],
            "resume_bullets": [],
        }
    )
    assert not ok

    ok, reason = _validate_advice(
        {
            "verdict": "Сильное совпадение по продуктовому опыту, но не хватает e-commerce кейсов.",
            "fit_readiness": "moderate",
            "resume_additions": [{"item": "Добавить метрики GMV", "why": "в вакансии", "effort": "quick"}],
        }
    )
    assert ok, reason


def test_normalize_advice_clamps_lists():
    raw = {
        "verdict": "  Вердикт  ",
        "fit_readiness": "unknown",
        "priority_action": "Дописать блок про маркетплейсы",
        "resume_additions": [
            {"item": " SQL ", "why": "нужен", "effort": "fast"},
            "skip",
        ],
        "resume_bullets": ["буллет 1", "", "буллет 2"],
        "interview_talking_points": ["пункт"],
        "honest_gaps": ["пробел"],
    }
    out = _normalize_advice(raw)
    assert out["fit_readiness"] == "moderate"
    assert out["resume_additions"][0]["effort"] == "medium"
    assert len(out["resume_bullets"]) == 2
