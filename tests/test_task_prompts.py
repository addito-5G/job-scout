"""Тесты реестра промптов."""

from __future__ import annotations

from ai.task_prompts import TASK_PROMPT_BUILDERS


def test_task_registry_has_cover_letter():
    assert "generate_cover_letter" in TASK_PROMPT_BUILDERS


def test_task_registry_has_vacancy_fit_advice():
    assert "vacancy_fit_advice" in TASK_PROMPT_BUILDERS
    prompt, system = TASK_PROMPT_BUILDERS["vacancy_fit_advice"](
        {
            "candidate_name": "Тест",
            "target_role": "product_manager",
            "resume_excerpt": "опыт",
            "profile_json": "{}",
            "vacancy_json": "{}",
            "fit_context_json": "{}",
        }
    )
    assert "Fit Score" in prompt
    assert system

    assert "fast_match" not in TASK_PROMPT_BUILDERS
    assert "match_vacancy_deep" not in TASK_PROMPT_BUILDERS
