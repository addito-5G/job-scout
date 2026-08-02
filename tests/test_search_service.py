"""Тесты генерации ключей поиска из профиля."""

from __future__ import annotations

import json

from db.tables import CandidateProfile
from services.search_service import (
    _defaults_from_profile,
    _normalize_hh_queries,
    settings_to_queries_from_data,
)


def _profile(**kwargs) -> CandidateProfile:
    profile = CandidateProfile()
    for key, value in kwargs.items():
        setattr(profile, key, value)
    return profile


def test_defaults_use_profile_title_not_pm_hardcode():
    profile = _profile(
        title="Data Engineer",
        recommended_roles_json=json.dumps(["Data Engineer", "ETL Developer"]),
        skills_json=json.dumps(["Python", "Spark"]),
    )
    data = _defaults_from_profile(profile)
    assert "product manager" not in [k.lower() for k in data["keywords_include"]]
    assert data["desired_titles"] == ["Data Engineer", "ETL Developer"]
    assert "Data Engineer" in data["keywords_include"]
    assert data["sources_enabled"] == {"hh_parser": True}


def test_settings_to_queries_from_profile_titles():
    queries = settings_to_queries_from_data(
        {"desired_titles": ["Backend Developer"], "work_formats": ["remote"]}
    )
    assert queries[0]["text"] == "Backend Developer"
    assert queries[0]["schedule"] == "remote"
    assert queries[0]["search_period"] == 7


def test_normalize_hh_queries_injects_search_period():
    normalized = _normalize_hh_queries([{"text": "PM", "area": 1}])
    assert normalized[0]["search_period"] == 7
    assert normalized[0]["text"] == "PM"
