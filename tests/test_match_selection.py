"""Тесты MatchSelection."""

from __future__ import annotations

from services.vacancy_service import MatchSelection, match_has_analysis, pick_best_match


def test_match_selection_pick_prefers_deep():
    fast = {"match_score": 90, "matched_skills": ["a"]}
    deep = {"match_score": 70, "matched_skills": ["b"]}
    sel = MatchSelection.pick(fast, deep)
    assert sel.level == "deep"
    assert sel.match is deep


def test_pick_best_match_tuple_compat():
    fast = {"match_score": 60, "match_summary": "ok"}
    sel_match, level = pick_best_match(fast, None)
    assert level == "fast"
    assert sel_match is fast


def test_match_has_analysis_false_for_letter_stub():
    assert match_has_analysis({"cover_letter_draft": "x", "match_score": 0}) is False
