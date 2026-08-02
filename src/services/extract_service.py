"""Извлечение ключей поиска из резюме."""

from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from db.models import CandidateProfile
from services.profile_service import parse_resume_upload
from services.search_service import build_search_draft

ProgressCallback = Callable[[float, str], None]


def extract_search_keys(
    session: Session,
    content: str,
    *,
    display_name: str,
    filename: str = "resume.pdf",
    source_bytes: bytes | None = None,
    progress: ProgressCallback | None = None,
) -> tuple[CandidateProfile, dict]:
    def _p(value: float, message: str) -> None:
        if progress:
            progress(value, message)

    _p(0.1, "Читаем текст резюме...")
    _p(0.25, "AI извлекает должность и навыки (Ollama)...")
    profile, _ = parse_resume_upload(
        session,
        content,
        display_name=display_name,
        filename=filename,
        source_bytes=source_bytes,
    )

    _p(0.6, "Анализируем профиль для рынка РФ...")
    _p(0.8, "Формируем ключи для hh.ru...")
    draft = build_search_draft(session, profile.id)

    _p(1.0, "Ключи готовы")
    return profile, draft
