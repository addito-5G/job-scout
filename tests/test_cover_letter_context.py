"""Тесты контекста cover letter (без вызова AI)."""

from __future__ import annotations

import json

from db.models import CandidateProfile
from services.cover_letter_context import first_name_from, profile_for_cover_letter_json


def _profile(**kwargs) -> CandidateProfile:
    defaults = {
        "full_name": "Андрей Накимов",
        "title": "Product Manager / Analyst",
        "experience_years": 7,
        "skills_json": json.dumps(
            ["Roadmap", "SQL", "CustDev", "ClickHouse"],
            ensure_ascii=False,
        ),
        "strengths_json": json.dumps(
            ["Запуск B2B SaaS с нуля", "Более 10 лет в IT"],
            ensure_ascii=False,
        ),
        "domains_json": json.dumps(["e-commerce", "SaaS"], ensure_ascii=False),
    }
    defaults.update(kwargs)
    return CandidateProfile(**defaults)


def test_first_name_extracts_first_token():
    assert first_name_from("Андрей Накимов") == "Андрей"


def test_profile_for_cover_letter_pm_splits_skills():
    raw = profile_for_cover_letter_json(_profile(), target_role="product_manager")
    data = json.loads(raw)
    assert data["first_name"] == "Андрей"
    assert "Roadmap" in data["pm_skills"]
    assert "SQL" in data["analyst_tools_supplement"]
    assert any("Запуск" in s for s in data["pm_achievements"])
    assert "Более 10 лет" not in " ".join(data["pm_achievements"])
