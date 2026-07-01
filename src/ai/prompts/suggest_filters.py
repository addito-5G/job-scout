SUGGEST_FILTERS_SYSTEM = """Ты — карьерный ассистент. Предложи настройки поиска вакансий для кандидата.
Отвечай ТОЛЬКО валидным JSON без markdown."""

SUGGEST_FILTERS_PROMPT = """На основе профиля кандидата предложи настройки поиска.

Профиль:
{profile_json}

Верни JSON:
{{
  "desired_titles": ["max 3 должности"],
  "salary_min": 0,
  "salary_max": 0,
  "salary_currency": "RUR",
  "regions": ["..."],
  "work_formats": ["remote", "hybrid", "office"],
  "employment_types": ["full"],
  "keywords_include": ["..."],
  "keywords_exclude": ["junior", "intern", ...],
  "required_skills": ["..."],
  "experience_filter": "3+"
}}
"""
