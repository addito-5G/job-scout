"""Тесты реестра промптов."""

from __future__ import annotations

from ai.task_prompts import TASK_PROMPT_BUILDERS


def test_task_registry_has_cover_letter():
    assert "generate_cover_letter" in TASK_PROMPT_BUILDERS


def test_task_registry_no_legacy_match_tasks():
    assert "fast_match" not in TASK_PROMPT_BUILDERS
    assert "match_vacancy_deep" not in TASK_PROMPT_BUILDERS
