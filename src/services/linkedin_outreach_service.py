"""Генерация сообщения для мягкого входа в LinkedIn (ручная отправка)."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from sqlalchemy.orm import Session

from ai import AIRouter
from ai.ai_router import AIRouterError
from ai.prompts.linkedin_outreach import LINKEDIN_OUTREACH_PROMPT_VERSION
from db.models import CandidateProfile, Vacancy
from domain.role import infer_target_role
from services.cover_letter_context import (
    first_name_from,
    match_context_for_cover_letter,
    profile_for_outreach_json,
)
from services.cover_letter_service import _get_match_for_letter
from services.match_service import vacancy_to_json

_OUTREACH_MAX_CHARS = 580
_OUTREACH_BANNED_PATTERNS = [
    r"хочу откликнуться[^.!\n]*[.!]?\s*",
    r"ищу работу[^.!\n]*[.!]?\s*",
    r"рассмотрите (?:моё )?резюме[^.!\n]*[.!]?\s*",
    r"буду рад стать частью команды[^.!\n]*[.!]?\s*",
    r"идеально подхожу[^.!\n]*[.!]?\s*",
    r"уверен, что буду полезен[^.!\n]*[.!]?\s*",
    r"мой богатый опыт[^.!\n]*[.!]?\s*",
    r"уверен, что мои навыки[^.!\n]*[.!]?\s*",
    r"спасибо за ваше время[^.!\n]*[.!]?\s*",
]


def normalize_outreach(text: str, profile: CandidateProfile) -> str:
    """Постобработка черновика: имя, запреты, markdown, длина."""
    letter = (text or "").strip()
    if not letter:
        return letter

    letter = re.sub(r"\*\*([^*]+)\*\*", r"\1", letter)
    letter = re.sub(r"^#+\s*", "", letter, flags=re.MULTILINE)

    full_name = (profile.full_name or "").strip()
    first = first_name_from(full_name)
    if first != "кандидат" and full_name:
        letter = letter.replace(full_name, first)
        if " " in full_name:
            surname = full_name.split()[-1]
            letter = re.sub(
                rf"\b{re.escape(first)}\s+{re.escape(surname)}\b",
                first,
                letter,
                flags=re.IGNORECASE,
            )

    for pattern in _OUTREACH_BANNED_PATTERNS:
        letter = re.sub(pattern, "", letter, flags=re.IGNORECASE)

    letter = re.sub(r"\n{3,}", "\n\n", letter).strip()
    letter = re.sub(r"!{2,}", "!", letter)

    if len(letter) > _OUTREACH_MAX_CHARS:
        cut = letter[:_OUTREACH_MAX_CHARS]
        last_stop = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        letter = cut[: last_stop + 1].strip() if last_stop > 200 else cut.rstrip() + "…"

    return letter.strip()


def linkedin_people_search_url(
    *,
    company: str,
    vacancy_title: str,
    contact_role: str = "recruiter",
) -> str:
    """Публичная ссылка на поиск людей — пользователь открывает и пишет сам."""
    role_hint = {
        "recruiter": "recruiter OR talent OR HR",
        "hiring_manager": "hiring manager OR head of product",
        "team_lead": "team lead OR engineering manager",
        "founder": "founder OR CEO OR CPO",
        "peer": "product manager OR product lead",
    }.get(contact_role, "recruiter")
    keywords = f"{company} {role_hint} {vacancy_title}".strip()
    return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(keywords)}"


def generate_linkedin_outreach(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    contact_role: str = "recruiter",
    use_cache: bool = False,
) -> str:
    router = AIRouter(session)
    target_role = infer_target_role(vacancy.title)
    match = _get_match_for_letter(session, vacancy.id, profile.id)
    company_name = vacancy.company_rel.name if vacancy.company_rel else ""

    payload = {
        "prompt_version": LINKEDIN_OUTREACH_PROMPT_VERSION,
        "target_role": target_role,
        "contact_role": contact_role,
        "profile_id": profile.id,
        "vacancy_id": vacancy.id,
        "profile_json": profile_for_outreach_json(profile, target_role=target_role),
        "vacancy_json": vacancy_to_json(session, vacancy),
        "match_context_json": match_context_for_cover_letter(match),
        "company_name": company_name,
        "vacancy_title": vacancy.title,
        "candidate_first_name": first_name_from(profile.full_name),
    }
    result = router.route("generate_linkedin_outreach", payload, parse_json=False, use_cache=use_cache)
    text = normalize_outreach((result.content or "").strip(), profile)
    if not text:
        raise AIRouterError("Пустой ответ от AI")
    return text
