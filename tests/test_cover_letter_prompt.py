"""Тесты промпта сопроводительного письма v10."""

from __future__ import annotations

import json

from ai.prompts.cover_letter import (
    COVER_LETTER_PROMPT_VERSION,
    apply_channel_guidance,
    format_cover_letter_prompt,
)
from ai.task_prompts import build_task_prompt


def test_cover_letter_prompt_version_bumped():
    assert COVER_LETTER_PROMPT_VERSION == "10"


def test_apply_channel_guidance_same_platform_hh():
    text = apply_channel_guidance("hh", apply_channel="same")
    assert "HeadHunter" in text
    assert "избыточно" in text.lower() or "НЕ пиши" in text


def test_format_prompt_name_from_resume_and_variability():
    prompt = format_cover_letter_prompt(
        example="ex",
        target_role_label="PM",
        role_guidance="rg",
        apply_channel_guidance=apply_channel_guidance("hh"),
        candidate_role_title="Product Manager",
        profile_json=json.dumps({"full_name": "Накимов Андрей", "resume_header_excerpt": "Андрей"}),
        vacancy_json="{}",
        match_context_json="{}",
    )
    assert "resume_header_excerpt" in prompt or "full_name" in prompt
    assert "Фамилия Имя" in prompt or "не фамилию" in prompt
    assert "варьируй" in prompt.lower() or "вариатив" in prompt.lower()
    assert "не перечисляй" in prompt.lower() or "каталог" in prompt.lower()


def test_build_cover_letter_injects_same_platform_rule():
    prompt, _ = build_task_prompt(
        "generate_cover_letter",
        {
            "target_role": "product_manager",
            "profile_json": json.dumps(
                {
                    "full_name": "Накимов Андрей",
                    "role_title": "Product Manager",
                    "resume_header_excerpt": "Андрей Накимов, Product Manager",
                }
            ),
            "vacancy_json": json.dumps({"source": "hh", "title": "PM", "description": "Discovery"}),
            "match_context_json": "{}",
        },
    )
    assert "HeadHunter" in prompt
    assert "Накимов" in prompt  # в запретах, не как имя для подстановки
    assert "resume_header_excerpt" in prompt or "full_name" in prompt
