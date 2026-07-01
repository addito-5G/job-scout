from __future__ import annotations

"""Маршрутизация AI-задач по провайдерам."""

# primary provider per task; fallback chain handled in ai_router
TASK_ROUTING: dict[str, str] = {
    "parse_resume": "ollama",
    "extract_skills": "ollama",
    "extract_skills_ru": "yandex",
    "categorize_vacancy": "ollama",
    "fast_match": "ollama",
    "analyze_resume_ru": "yandex",
    "match_vacancy_deep": "groq",
    "profile_gaps": "groq",
    "improve_resume": "groq",
    "generate_cover_letter": "yandex",
    "suggest_filters": "ollama",
}

FALLBACK_CHAIN: dict[str, list[str]] = {
    "ollama": ["yandex", "groq"],
    "yandex": ["groq", "ollama"],
    "groq": ["yandex", "ollama"],
}

# TTL in days per task type
CACHE_TTL_DAYS: dict[str, int] = {
    "parse_resume": 7,
    "analyze_resume_ru": 7,
    "extract_skills": 30,
    "extract_skills_ru": 30,
    "fast_match": 14,
    "match_vacancy_deep": 14,
    "improve_resume": 7,
    "default": 30,
}
