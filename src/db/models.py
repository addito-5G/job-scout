"""Публичный API слоя БД (re-export tables + engine)."""

from db.engine import get_engine, get_session, get_session_factory, init_db, resolve_database_url
from db.tables import (
    AICache,
    AIUsageLog,
    Base,
    CandidateProfile,
    Company,
    DailyMetrics,
    Location,
    ScanRun,
    SearchSettings,
    Skill,
    Vacancy,
    VacancyMatch,
    VacancySkill,
    VacancyTag,
)

__all__ = [
    "AICache",
    "AIUsageLog",
    "Base",
    "CandidateProfile",
    "Company",
    "DailyMetrics",
    "Location",
    "ScanRun",
    "SearchSettings",
    "Skill",
    "Vacancy",
    "VacancyMatch",
    "VacancySkill",
    "VacancyTag",
    "get_engine",
    "get_session",
    "get_session_factory",
    "init_db",
    "resolve_database_url",
]
