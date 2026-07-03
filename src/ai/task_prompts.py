"""Реестр построителей промптов для AIRouter (без изменения текстов)."""

from __future__ import annotations

import json
from typing import Any, Callable

PromptBuilder = Callable[[dict[str, Any]], tuple[str, str | None]]


def _build_parse_resume(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.parse_resume import PARSE_RESUME_PROMPT, PARSE_RESUME_SYSTEM

    return (
        PARSE_RESUME_PROMPT.format(resume_text=payload.get("resume_text", "")),
        PARSE_RESUME_SYSTEM,
    )


def _build_analyze_resume_ru(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.parse_resume import ANALYZE_RESUME_RU_PROMPT, ANALYZE_RESUME_RU_SYSTEM

    return (
        ANALYZE_RESUME_RU_PROMPT.format(resume_text=payload.get("resume_text", "")),
        ANALYZE_RESUME_RU_SYSTEM,
    )


def _build_suggest_filters(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.suggest_filters import SUGGEST_FILTERS_PROMPT, SUGGEST_FILTERS_SYSTEM

    return (
        SUGGEST_FILTERS_PROMPT.format(profile_json=payload.get("profile_json", "{}")),
        SUGGEST_FILTERS_SYSTEM,
    )


def _build_fast_match(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.match_vacancy import FAST_MATCH_PROMPT, FAST_MATCH_SYSTEM

    return (
        FAST_MATCH_PROMPT.format(
            profile_json=payload.get("profile_json", "{}"),
            vacancy_json=payload.get("vacancy_json", "{}"),
        ),
        FAST_MATCH_SYSTEM,
    )


def _build_deep_match(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.match_vacancy import DEEP_MATCH_PROMPT, DEEP_MATCH_SYSTEM

    return (
        DEEP_MATCH_PROMPT.format(
            profile_json=payload.get("profile_json", "{}"),
            vacancy_json=payload.get("vacancy_json", "{}"),
        ),
        DEEP_MATCH_SYSTEM,
    )


def _build_cover_letter(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.cover_letter import (
        COVER_LETTER_EXAMPLE,
        COVER_LETTER_SYSTEM,
        ROLE_SKILL_GUIDANCE,
        TARGET_ROLE_LABELS,
        format_cover_letter_prompt,
    )

    target_role = payload.get("target_role", "general")
    profile_data = json.loads(payload.get("profile_json", "{}"))
    return (
        format_cover_letter_prompt(
            example=COVER_LETTER_EXAMPLE,
            target_role_label=TARGET_ROLE_LABELS.get(target_role, TARGET_ROLE_LABELS["general"]),
            role_guidance=ROLE_SKILL_GUIDANCE.get(target_role, ROLE_SKILL_GUIDANCE["general"]),
            candidate_first_name=profile_data.get("first_name", "кандидат"),
            candidate_role_title=profile_data.get("role_title", "специалист"),
            profile_json=payload.get("profile_json", "{}"),
            vacancy_json=payload.get("vacancy_json", "{}"),
            match_context_json=payload.get("match_context_json", "{}"),
        ),
        COVER_LETTER_SYSTEM,
    )


def _build_improve_resume(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.improve_resume import IMPROVE_RESUME_PROMPT, IMPROVE_RESUME_SYSTEM

    return (
        IMPROVE_RESUME_PROMPT.format(
            resume_text=payload.get("resume_text", ""),
            profile_json=payload.get("profile_json", "{}"),
            market_requirements_json=payload.get("market_requirements_json", "{}"),
            vacancy_count=payload.get("vacancy_count", 0),
        ),
        IMPROVE_RESUME_SYSTEM,
    )


TASK_PROMPT_BUILDERS: dict[str, PromptBuilder] = {
    "parse_resume": _build_parse_resume,
    "analyze_resume_ru": _build_analyze_resume_ru,
    "suggest_filters": _build_suggest_filters,
    "fast_match": _build_fast_match,
    "match_vacancy_deep": _build_deep_match,
    "generate_cover_letter": _build_cover_letter,
    "improve_resume": _build_improve_resume,
}


def build_task_prompt(task_type: str, payload: dict[str, Any]) -> tuple[str, str | None]:
    builder = TASK_PROMPT_BUILDERS.get(task_type)
    if builder:
        return builder(payload)
    if "prompt" in payload:
        return payload["prompt"], payload.get("system")
    raise ValueError(f"Неизвестный payload для задачи {task_type}")
