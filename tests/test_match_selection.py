"""Тесты выбора лучшего match."""

from __future__ import annotations

from services.vacancy_service.match_view import match_has_analysis, pick_best_match


def test_pick_best_match_prefers_first_with_analysis():
    fit = {"match_score": 80, "matched_skills": ["a"], "match_summary": "fit"}
    legacy = {"match_score": 90, "matched_skills": ["b"], "match_summary": "legacy"}
    assert pick_best_match(fit, legacy) is fit


def test_match_has_analysis_false_for_empty_stub():
    stub = {"cover_letter_draft": "text", "match_score": 0}
    assert match_has_analysis(stub) is False
