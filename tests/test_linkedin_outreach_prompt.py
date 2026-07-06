"""Тесты построения промпта LinkedIn outreach."""

from __future__ import annotations

from ai.prompts.linkedin_outreach import (
    LINKEDIN_OUTREACH_EXAMPLE,
    LINKEDIN_OUTREACH_PROMPT_VERSION,
    format_linkedin_outreach_prompt,
)
from ai.task_prompts import TASK_PROMPT_BUILDERS, build_task_prompt


def test_outreach_prompt_version():
    assert LINKEDIN_OUTREACH_PROMPT_VERSION == "1-final-soft-networking"


def test_task_registry_has_linkedin_outreach():
    assert "generate_linkedin_outreach" in TASK_PROMPT_BUILDERS


def test_format_outreach_prompt_includes_context_and_readability_rules():
    prompt = format_linkedin_outreach_prompt(
        example=LINKEDIN_OUTREACH_EXAMPLE,
        candidate_first_name="Андрей",
        contact_role="founder",
        company_name="KTS",
        vacancy_title="Product Manager",
        profile_json="{}",
        vacancy_json='{"title":"PM"}',
        match_context_json="{}",
    )
    assert "Андрей" in prompt
    assert "KTS" in prompt
    assert "ЛЁГКОСТЬ ЧТЕНИЯ" in prompt
    assert "фаундер" in prompt.lower() or "executive" in prompt.lower()


def test_build_linkedin_outreach_uses_example():
    prompt, system = build_task_prompt(
        "generate_linkedin_outreach",
        {
            "contact_role": "peer",
            "company_name": "Acme",
            "vacancy_title": "PM",
            "profile_json": '{"first_name": "Андрей"}',
            "vacancy_json": "{}",
            "match_context_json": "{}",
        },
    )
    assert "builder mindset" in prompt or "созидатель" in prompt
    assert "легк" in system.lower() or "лёгк" in system.lower()
