"""Изменение user_status вакансии (application service для UI и скриптов)."""

from __future__ import annotations

from db import session_scope
from services.vacancy_service import update_vacancy_status


def set_vacancy_status(vacancy_id: int, status: str) -> bool:
    """Обновить статус вакансии и закоммитить в БД."""
    with session_scope() as session:
        return update_vacancy_status(session, vacancy_id, status)
