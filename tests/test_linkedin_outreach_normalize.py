"""Тесты постобработки LinkedIn outreach."""

from __future__ import annotations

from services.cover_letter_context import profile_for_outreach_json
from services.linkedin_outreach_service import normalize_outreach


class _Profile:
    full_name = "Андрей Накимов"
    experience_years = 12
    skills_json = '["Product Management", "SQL"]'
    domains_json = '["B2B"]'
    strengths_json = '["Запустил платформу"]'
    recommended_roles_json = '["Product Manager"]'
    ai_summary = "Продуктовый лидер с опытом B2B."
    experience_summary = None
    title = "Product Manager"


def test_normalize_outreach_strips_banned_and_surname():
    raw = (
        "Здравствуйте! Хочу откликнуться на вакансию. "
        "Я Андрей Накимов, ищу работу в продукте. "
        "Буду рад стать частью команды!"
    )
    out = normalize_outreach(raw, _Profile())
    assert "Накимов" not in out
    assert "откликнуться" not in out.lower()
    assert "ищу работу" not in out.lower()
    assert "Андрей" in out


def test_normalize_outreach_trims_markdown():
    out = normalize_outreach("**Привет!** Как дела?", _Profile())
    assert "**" not in out
    assert "Привет!" in out


def test_profile_for_outreach_json_includes_summary_and_angles():
    payload = profile_for_outreach_json(_Profile(), target_role="product_manager")
    assert "builder_angles" in payload
    assert "B2B" in payload
    assert "Продуктовый лидер" in payload
