"""Запись вакансий: upsert, статус, cover letter."""

from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import SearchSettings
from db.repositories.vacancy_repo import get_vacancy_by_id, upsert_vacancy
from models import Vacancy as VacancyDTO
from services.profile_filter_service import infer_role_from_settings
from time_utils import utc_now


def upsert_scored_vacancy(
    session: Session,
    vacancy: VacancyDTO,
    *,
    search_settings_id: int | None = None,
) -> tuple[int, bool]:
    profile_role: str | None = None
    if search_settings_id is not None:
        settings = session.get(SearchSettings, search_settings_id)
        if settings:
            profile_role = infer_role_from_settings(settings)
    return upsert_vacancy(
        session,
        vacancy,
        search_settings_id=search_settings_id,
        profile_role=profile_role,
    )


def update_vacancy_status(session: Session, vacancy_id: int, status: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    v.user_status = status
    v.updated_at = utc_now()
    session.commit()
    return True


def save_vacancy_cover_letter(session: Session, vacancy_id: int, letter: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    if v.matches:
        for m in v.matches:
            if m.match_level == "deep":
                m.cover_letter_draft = letter
    session.commit()
    return True
