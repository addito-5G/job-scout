from __future__ import annotations

import re

from sqlalchemy.orm import Session

import config
from ai import AIRouter
from ai.ai_router import AIRouterError
from ai.prompts.cover_letter import COVER_LETTER_PROMPT_VERSION
from db.models import CandidateProfile, Vacancy
from db.repositories.match_repo import get_match, save_cover_letter_draft
from domain.role import infer_target_role
from services.cover_letter_context import (
    match_context_for_cover_letter,
    profile_for_cover_letter_json,
)
from services.match_service import vacancy_to_json

# Re-export для обратной совместимости.
__all__ = ["infer_target_role", "generate_cover_letter", "normalize_cover_letter"]

_CONTACTS_LINE_RE = re.compile(r"^\s*мои контакты\s*:", re.IGNORECASE)


def _get_match_for_letter(session: Session, vacancy_id: int, profile_id: int):
    for level in ("fit", "deep", "fast"):
        match = get_match(session, vacancy_id, profile_id, level)
        if match:
            return match
    return None


def format_contacts_block() -> str:
    lines = ["Мои контакты:"]
    if config.CONTACT_PHONE:
        lines.append(config.CONTACT_PHONE)
    if config.CONTACT_TELEGRAM:
        lines.append(f"tg @{config.CONTACT_TELEGRAM.lstrip('@')}")
    if config.CONTACT_LINKEDIN:
        link = config.CONTACT_LINKEDIN
        if not link.startswith("http"):
            link = f"https://{link.removeprefix('www.')}"
        lines.append(link)
    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def _strip_ai_contacts(letter: str) -> str:
    lines = letter.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if _CONTACTS_LINE_RE.match(lines[i]):
            return "\n".join(lines[:i]).rstrip()
    return letter.rstrip()


def _normalize_letter(letter: str, profile: CandidateProfile) -> str:
    """Лёгкая постобработка: клише и форматирование. Имя — на стороне AI из резюме."""
    letter = re.sub(
        r"у меня более\s+\d+\s+лет опыта[^,]+,\s*",
        "",
        letter,
        flags=re.IGNORECASE,
    )
    letter = re.sub(
        r"^у меня более\s+\d+\s+лет[^.!\n]*[.!]\s*",
        "",
        letter,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if profile.experience_years:
        letter = re.sub(
            rf"за более чем\s+{profile.experience_years}\s+лет[^.!\n]*[.!]\s*",
            "",
            letter,
            flags=re.IGNORECASE,
        )

    banned = [
        r"уверен, что мои навыки[^.!\n]*[.!]\s*",
        r"я приобрёл глубокие знания[^.!\n]*[.!]\s*",
        r"владею различными инструментами[^.!\n]*[.!]\s*",
        r"меня заинтересовала возможность поработать[^.!\n]*[.!]\s*",
        r"меня заинтересовала возможность[^.!\n]*[.!]\s*",
        r"спасибо за ваше время[^.!\n]*[.!]?\s*",
        r"крупной и уважаемой компании[^.!\n]*[.!]\s*",
    ]
    for pattern in banned:
        letter = re.sub(pattern, "", letter, flags=re.IGNORECASE)

    return re.sub(r"\n{3,}", "\n\n", letter).strip()


def normalize_cover_letter(letter: str, profile: CandidateProfile) -> str:
    """Публичная обёртка над post-processing письма (v8, без изменения логики)."""
    return _normalize_letter(letter, profile)


def _append_contacts(letter: str) -> str:
    contacts = format_contacts_block()
    if not contacts:
        return letter
    body = _strip_ai_contacts(letter)
    return f"{body}\n\n{contacts}" if body else contacts


def generate_cover_letter(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    save: bool = True,
    use_cache: bool = False,
) -> str:
    router = AIRouter(session)
    target_role = infer_target_role(vacancy.title)
    match = _get_match_for_letter(session, vacancy.id, profile.id)
    payload = {
        "prompt_version": COVER_LETTER_PROMPT_VERSION,
        "target_role": target_role,
        "profile_id": profile.id,
        "vacancy_id": vacancy.id,
        "profile_json": profile_for_cover_letter_json(profile, target_role=target_role),
        "vacancy_json": vacancy_to_json(session, vacancy),
        "match_context_json": match_context_for_cover_letter(match),
    }
    result = router.route("generate_cover_letter", payload, parse_json=False, use_cache=use_cache)
    letter = _normalize_letter((result.content or "").strip(), profile)
    letter = _append_contacts(letter)
    if not letter:
        raise AIRouterError("Пустой ответ от AI")
    if save:
        save_cover_letter_draft(session, vacancy.id, profile.id, letter)
    return letter
