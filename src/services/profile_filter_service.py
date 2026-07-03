"""Фильтрация вакансий и аналитики по роли профиля (из должности в резюме)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from db.models import CandidateProfile, ScanRun, SearchSettings, Vacancy
from domain.role import (
    DEFAULT_ROLE_LABELS,
    ROLE_PRODUCT_ANALYST,
    ROLE_PRODUCT_MANAGER,
    infer_role_from_title,
    role_label,
)
from services.profile_serialization import loads_json as _loads

# Re-export для обратной совместимости.
__all__ = [
    "ROLE_PRODUCT_ANALYST",
    "ROLE_PRODUCT_MANAGER",
    "DEFAULT_ROLE_LABELS",
    "infer_role_from_title",
    "infer_role_from_settings",
    "role_label",
]


def infer_role_from_settings(settings: SearchSettings) -> str | None:
    titles = _loads(settings.desired_titles_json, [])
    for title in titles[:3]:
        role = infer_role_from_title(str(title))
        if role:
            return role
    if settings.profile_label:
        return infer_role_from_title(settings.profile_label)
    return None


def settings_label(settings: SearchSettings) -> str:
    role = infer_role_from_settings(settings)
    if role and role in DEFAULT_ROLE_LABELS:
        return DEFAULT_ROLE_LABELS[role]
    titles = _loads(settings.desired_titles_json, [])
    if titles:
        return str(titles[0])
    if settings.profile_label:
        return settings.profile_label
    return f"Профиль #{settings.id}"


def list_profile_filters(session: Session, profile_id: int) -> list[dict[str, Any]]:
    """Целевые должности из резюме и настроек поиска (не отдельные CV)."""
    filters: dict[str, dict[str, Any]] = {}

    profile = session.get(CandidateProfile, profile_id)
    if profile:
        seed_titles = [profile.title] if profile.title else []
        seed_titles.extend(str(t) for t in _loads(profile.recommended_roles_json, []) if t)
        for title in seed_titles:
            role = infer_role_from_title(str(title))
            if not role or role in filters:
                continue
            filters[role] = {
                "role": role,
                "label": str(title).strip(),
                "is_active": False,
            }

    rows = session.execute(
        select(SearchSettings)
        .where(SearchSettings.profile_id == profile_id)
        .order_by(SearchSettings.is_active.desc(), SearchSettings.created_at.desc())
    ).scalars().all()

    for row in rows:
        role = infer_role_from_settings(row)
        if not role or role in filters:
            continue
        filters[role] = {
            "role": role,
            "label": settings_label(row),
            "is_active": bool(row.is_active),
        }

    for role, count in session.execute(
        select(Vacancy.profile_role, func.count())
        .where(Vacancy.profile_role.isnot(None), Vacancy.is_active.is_(True))
        .group_by(Vacancy.profile_role)
    ).all():
        if role and role not in filters:
            filters[role] = {
                "role": role,
                "label": role_label(role),
                "is_active": False,
            }

    ordered = [ROLE_PRODUCT_MANAGER, ROLE_PRODUCT_ANALYST]
    result = [filters[r] for r in ordered if r in filters]
    extras = sorted(
        (item for role, item in filters.items() if role not in ordered),
        key=lambda x: x["label"].lower(),
    )
    return result + extras


def get_active_filter_role(session: Session, profile_id: int) -> str | None:
    profile = session.get(CandidateProfile, profile_id)
    if profile and profile.title:
        role = infer_role_from_title(profile.title)
        if role:
            return role

    active = session.execute(
        select(SearchSettings)
        .where(SearchSettings.profile_id == profile_id, SearchSettings.is_active.is_(True))
        .order_by(SearchSettings.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if active:
        return infer_role_from_settings(active)
    return None


def filter_keywords(settings: SearchSettings) -> list[str]:
    titles = _loads(settings.desired_titles_json, [])
    include = _loads(settings.keywords_include_json, [])
    words: list[str] = []
    for item in [*titles[:3], *include[:8]]:
        token = str(item).strip()
        if len(token) >= 3:
            words.append(token)
    return words


def vacancy_matches_role(vacancy: Vacancy, role: str) -> bool:
    if vacancy.profile_role == role:
        return True
    if vacancy.profile_role is not None:
        return False
    inferred = infer_role_from_title(vacancy.title)
    return inferred == role


def vacancy_scope_condition(profile_role: str | None) -> ColumnElement[bool] | None:
    if profile_role is None:
        return None
    return Vacancy.profile_role == profile_role


def _role_from_settings_row(settings_by_id: dict[int, SearchSettings], settings_id: int | None) -> str | None:
    if settings_id is None:
        return None
    settings = settings_by_id.get(settings_id)
    if not settings:
        return None
    return infer_role_from_settings(settings)


def backfill_profile_roles(session: Session) -> dict[str, int]:
    stats = {"by_scan": 0, "by_settings": 0, "by_title": 0, "unchanged": 0}
    settings_by_id = {
        row.id: row for row in session.execute(select(SearchSettings)).scalars().all()
    }

    for run in session.execute(select(ScanRun).where(ScanRun.search_settings_id.isnot(None))).scalars():
        role = _role_from_settings_row(settings_by_id, run.search_settings_id)
        if not role or not run.started_at:
            continue
        end = run.finished_at or run.started_at
        rows = session.execute(
            select(Vacancy).where(
                Vacancy.scraped_at >= run.started_at,
                Vacancy.scraped_at <= end,
                Vacancy.profile_role.is_(None),
            )
        ).scalars().all()
        for v in rows:
            v.profile_role = role
            if run.search_settings_id and v.search_settings_id is None:
                v.search_settings_id = run.search_settings_id
            stats["by_scan"] += 1

    for v in session.execute(
        select(Vacancy).where(Vacancy.profile_role.is_(None), Vacancy.search_settings_id.isnot(None))
    ).scalars():
        role = _role_from_settings_row(settings_by_id, v.search_settings_id)
        if role:
            v.profile_role = role
            stats["by_settings"] += 1

    for v in session.execute(select(Vacancy).where(Vacancy.profile_role.is_(None))).scalars():
        role = infer_role_from_title(v.title)
        if role:
            v.profile_role = role
            stats["by_title"] += 1
        else:
            stats["unchanged"] += 1

    session.commit()
    return stats


def backfill_vacancy_settings(session: Session) -> dict[str, int]:
    """Совместимость: проставляет profile_role и search_settings_id."""
    return backfill_profile_roles(session)


def snapshot_profile_labels(session: Session, profile_id: int) -> None:
    profile = session.get(CandidateProfile, profile_id)
    if not profile or not profile.title:
        return
    role = infer_role_from_title(profile.title)
    label = profile.title
    for row in session.execute(
        select(SearchSettings).where(
            SearchSettings.profile_id == profile_id,
            SearchSettings.is_active.is_(True),
        )
    ).scalars():
        row.profile_label = label
        if role:
            row.profile_label = role_label(role)
    session.commit()
