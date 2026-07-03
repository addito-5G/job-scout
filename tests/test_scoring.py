"""Smoke-тесты для rule-based скоринга."""

from __future__ import annotations

from models import Vacancy
from scoring import score_vacancy

_CRITERIA = {
    "must_match": ["product manager", "продакт", "product owner"],
    "boost": ["saas", "b2b"],
    "penalty": ["junior", "intern"],
    "locations": ["москва", "remote"],
    "thresholds": {"max_age_days": 14, "min_score": 0},
}


def test_score_zero_without_must_match_keywords():
    v = Vacancy(
        source="hh",
        external_id="1",
        title="Backend Developer",
        description="Python, Django, REST API",
    )
    result = score_vacancy(v, _CRITERIA)
    assert result.score == 0
    assert "нет ключевых слов" in result.score_reasons[0]


def test_score_positive_with_pm_title_and_boost():
    v = Vacancy(
        source="hh",
        external_id="2",
        title="Product Manager",
        description="B2B SaaS, roadmap, backlog",
        skills=["roadmap", "Jira"],
    )
    result = score_vacancy(v, _CRITERIA)
    assert result.score >= 30
    assert any("роль PM" in r for r in result.score_reasons)


def test_penalty_keywords_reduce_score():
    v = Vacancy(
        source="hh",
        external_id="3",
        title="Junior Product Manager",
        description="продакт, стажировка",
    )
    result = score_vacancy(v, _CRITERIA)
    assert any("junior" in r.lower() for r in result.score_reasons)
