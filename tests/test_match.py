"""Тесты выбора лучшего match и парсинга AI-ответа."""

from __future__ import annotations

from services.match_service import _parse_match_result
from services.vacancy_service import match_has_analysis, pick_best_match


def test_parse_match_result_valid_schema():
    parsed = {
        "match_score": 82,
        "match_summary": "Хороший fit",
        "matched_skills": ["roadmap"],
        "missing_skills": ["fintech"],
        "recommendation": "apply",
    }
    result = _parse_match_result(parsed)
    assert result["match_score"] == 82
    assert result["recommendation"] == "apply"


def test_parse_match_result_empty_returns_fallback():
    result = _parse_match_result(None)
    assert result["match_score"] == 0
    assert result["recommendation"] == "skip"


def test_pick_best_match_prefers_deep():
    fast = {"match_score": 90, "match_summary": "fast", "matched_skills": ["a"]}
    deep = {"match_score": 75, "match_summary": "deep", "matched_skills": ["b"]}
    match, level = pick_best_match(fast, deep)
    assert level == "deep"
    assert match is deep


def test_pick_best_match_falls_back_to_fast():
    fast = {"match_score": 60, "match_summary": "ok", "matched_skills": ["x"]}
    deep = {"cover_letter_draft": "letter only"}
    match, level = pick_best_match(fast, deep)
    assert level == "fast"
    assert match is fast


def test_match_has_analysis_false_for_empty_stub():
    stub = {"cover_letter_draft": "text", "match_score": 0}
    assert match_has_analysis(stub) is False
