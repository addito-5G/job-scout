#!/usr/bin/env python3
"""Миграция данных из legacy-схемы в нормализованную v2."""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import config
from db import get_session, init_db
from db.entities import sync_vacancy_skills, sync_vacancy_tags, upsert_company, upsert_location
from db.models import (
    AICache,
    AIUsageLog,
    CandidateProfile,
    DailyMetrics,
    ScanRun,
    SearchSettings,
    Vacancy,
    VacancyMatch,
)
from db.normalize import normalize_source, parse_datetime

DB_PATH = config.ROOT / "data" / "vacancies.db"


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def _fetch_all(conn: sqlite3.Connection, table: str) -> list[dict]:
    if not _table_exists(conn, table):
        return []
    cols = _columns(conn, table)
    return [dict(zip(cols, row)) for row in conn.execute(f"SELECT * FROM {table}")]


def is_legacy_schema(conn: sqlite3.Connection) -> bool:
    if not _table_exists(conn, "vacancies"):
        return False
    cols = set(_columns(conn, "vacancies"))
    return "company" in cols and "company_id" not in cols


def backup_db() -> Path:
    backup = DB_PATH.with_suffix(f".db.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup)
        print(f"📦 Backup: {backup}")
    return backup


def drop_legacy_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=OFF")
    for table in [
        "vacancy_matches",
        "vacancy_skills",
        "vacancy_tags",
        "vacancies",
        "search_settings",
        "candidate_profile",
        "candidate_profiles",
        "companies",
        "locations",
        "skills",
        "ai_cache",
        "ai_usage_log",
        "scan_runs",
        "daily_metrics",
    ]:
        if _table_exists(conn, table):
            conn.execute(f"DROP TABLE {table}")
    conn.commit()


def migrate_profiles(session, conn: sqlite3.Connection) -> dict[int, int]:
    mapping: dict[int, int] = {}
    table = "candidate_profile" if _table_exists(conn, "candidate_profile") else None
    if not table:
        return mapping
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").description]
    for row in rows:
        data = dict(zip(cols, row))
        profile = CandidateProfile(
            resume_path=data.get("resume_path"),
            resume_raw=data.get("resume_raw"),
            full_name=data.get("full_name"),
            title=data.get("title"),
            experience_years=data.get("experience_years"),
            skills_json=data.get("skills"),
            strengths_json=data.get("strengths"),
            weaknesses_json=data.get("weaknesses"),
            recommended_roles_json=data.get("recommended_roles"),
            ai_summary=data.get("ai_summary"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=data.get("salary_currency") or "RUR",
            is_active=True,
        )
        session.add(profile)
        session.flush()
        mapping[data["id"]] = profile.id
    session.commit()
    print(f"✅ Профили: {len(mapping)}")
    return mapping


def migrate_search_settings(session, conn, profile_map: dict[int, int]) -> None:
    if not _table_exists(conn, "search_settings"):
        return
    rows = conn.execute("SELECT * FROM search_settings").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(search_settings)").description]
    count = 0
    for row in rows:
        data = dict(zip(cols, row))
        pid = profile_map.get(data.get("profile_id"))
        if not pid:
            continue
        session.add(
            SearchSettings(
                profile_id=pid,
                desired_titles_json=data.get("desired_titles"),
                salary_min=data.get("salary_min"),
                salary_max=data.get("salary_max"),
                salary_currency=data.get("salary_currency") or "RUR",
                keywords_include_json=data.get("keywords_include"),
                keywords_exclude_json=data.get("keywords_exclude"),
                required_skills_json=data.get("required_skills"),
                experience_filter=data.get("experience_filter"),
                work_formats_json=data.get("work_formats"),
                locations_json=data.get("regions"),
                employment_types_json=data.get("employment_types"),
                is_active=bool(data.get("active", True)),
            )
        )
        count += 1
    session.commit()
    print(f"✅ Search settings: {count}")


def migrate_vacancies(session, conn) -> dict[int, int]:
    mapping: dict[int, int] = {}
    rows = conn.execute("SELECT * FROM vacancies").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(vacancies)").description]
    for row in rows:
        data = dict(zip(cols, row))
        source = normalize_source(data.get("source") or "hh")
        company = upsert_company(session, source=source, name=data.get("company") or "Не указана")
        location = upsert_location(session, source=source, name=data.get("location") or "")

        desc_short = data.get("description") or ""
        desc_full = data.get("full_description") or desc_short

        skills: list[str] = []
        if data.get("skills"):
            try:
                skills = json.loads(data["skills"])
            except json.JSONDecodeError:
                pass

        published = parse_datetime(data.get("published_at"))
        enriched = parse_datetime(data.get("enriched_at"))

        vacancy = Vacancy(
            source=source,
            external_id=str(data.get("external_id") or data.get("id")),
            external_url=data.get("url") or f"{source}:{data.get('external_id')}",
            title=data.get("title") or "Без названия",
            company_id=company.id if company else None,
            description_short=desc_short,
            description_full=desc_full,
            salary_from=data.get("salary_min"),
            salary_to=data.get("salary_max"),
            salary_currency=data.get("salary_currency") or "RUR",
            salary_gross=bool(data.get("salary_gross")) if data.get("salary_gross") is not None else False,
            salary_text=data.get("salary"),
            work_format=data.get("work_format"),
            schedule=data.get("work_schedule"),
            employment=data.get("employment"),
            location_id=location.id if location else None,
            location_text=data.get("location"),
            experience_required=data.get("experience"),
            user_status=data.get("status") or "new",
            status="active",
            is_active=True,
            published_at=published,
            enriched_at=enriched,
            rule_score=data.get("score") or 0,
            rule_score_reasons=data.get("score_reasons"),
        )
        session.add(vacancy)
        session.flush()
        sync_vacancy_skills(session, vacancy.id, skills if isinstance(skills, list) else [])
        sync_vacancy_tags(session, vacancy.id, [])
        mapping[data["id"]] = vacancy.id
    session.commit()
    print(f"✅ Вакансии: {len(mapping)}")
    return mapping


def migrate_matches(session, conn, vacancy_map: dict[int, int], profile_map: dict[int, int]) -> None:
    if not _table_exists(conn, "vacancy_matches"):
        return
    rows = conn.execute("SELECT * FROM vacancy_matches").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(vacancy_matches)").description]
    count = 0
    for row in rows:
        data = dict(zip(cols, row))
        vid = vacancy_map.get(data.get("vacancy_id"))
        pid = profile_map.get(data.get("profile_id"))
        if not vid or not pid:
            continue
        session.add(
            VacancyMatch(
                vacancy_id=vid,
                profile_id=pid,
                match_score=float(data.get("match_score") or 0),
                match_level=data.get("match_level") or "fast",
                matched_skills_json=data.get("matched_skills"),
                missing_skills_json=data.get("missing_skills"),
                strengths_for_vacancy_json=data.get("strengths"),
                risks_json=data.get("risks"),
                recommendation=data.get("recommendation"),
                ai_analysis=data.get("deep_analysis") or data.get("match_summary"),
            )
        )
        count += 1
    session.commit()
    print(f"✅ Matches: {count}")


def migrate_ai_cache(session, conn) -> None:
    if not _table_exists(conn, "ai_cache"):
        return
    rows = conn.execute("SELECT * FROM ai_cache").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(ai_cache)").description]
    for row in rows:
        data = dict(zip(cols, row))
        session.add(
            AICache(
                cache_key=data["cache_key"],
                provider=data.get("provider") or "ollama",
                task_type=data.get("task_type") or "unknown",
                response=data.get("response") or "{}",
                tokens_used=data.get("tokens_used") or 0,
                expires_at=parse_datetime(data.get("expires_at")),
            )
        )
    session.commit()
    print(f"✅ AI cache: {len(rows)}")


def main() -> None:
    if not DB_PATH.exists():
        print("БД не найдена, создаём новую схему...")
        init_db()
        return

    conn = sqlite3.connect(DB_PATH)
    if not is_legacy_schema(conn):
        conn.close()
        init_db()
        session = get_session()
        total = session.execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM vacancies")).scalar()
        session.close()
        print(f"Схема уже v2. Вакансий: {total}")
        return

    print("🔄 Миграция legacy → v2...")
    backup_db()

    legacy_vacancies = _fetch_all(conn, "vacancies")
    profile_rows = _fetch_all(conn, "candidate_profile")
    settings_rows = _fetch_all(conn, "search_settings")
    match_rows = _fetch_all(conn, "vacancy_matches")
    cache_rows = _fetch_all(conn, "ai_cache")

    drop_legacy_tables(conn)
    conn.close()

    init_db()
    session = get_session()

    profile_map: dict[int, int] = {}
    path_to_new: dict[str, int] = {}
    for data in sorted(profile_rows, key=lambda x: str(x.get("updated_at") or ""), reverse=True):
        old_id = data["id"]
        path = data.get("resume_path") or f"legacy-{old_id}"
        if path in path_to_new:
            profile_map[old_id] = path_to_new[path]
            continue
        profile = CandidateProfile(
            resume_path=data.get("resume_path"),
            resume_raw=data.get("resume_raw"),
            full_name=data.get("full_name"),
            title=data.get("title"),
            experience_years=data.get("experience_years"),
            skills_json=data.get("skills"),
            strengths_json=data.get("strengths"),
            weaknesses_json=data.get("weaknesses"),
            recommended_roles_json=data.get("recommended_roles"),
            ai_summary=data.get("ai_summary"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=data.get("salary_currency") or "RUR",
        )
        session.add(profile)
        session.flush()
        profile_map[old_id] = profile.id
        if data.get("resume_path"):
            path_to_new[data["resume_path"]] = profile.id
    session.commit()
    print(f"✅ Профили: {len(path_to_new)} (записей legacy: {len(profile_rows)})")

    for data in settings_rows:
        pid = profile_map.get(data.get("profile_id"))
        if pid:
            session.add(
                SearchSettings(
                    profile_id=pid,
                    desired_titles_json=data.get("desired_titles"),
                    salary_min=data.get("salary_min"),
                    salary_max=data.get("salary_max"),
                    salary_currency=data.get("salary_currency") or "RUR",
                    keywords_include_json=data.get("keywords_include"),
                    keywords_exclude_json=data.get("keywords_exclude"),
                    required_skills_json=data.get("required_skills"),
                    experience_filter=data.get("experience_filter"),
                    work_formats_json=data.get("work_formats"),
                    locations_json=data.get("regions"),
                    employment_types_json=data.get("employment_types"),
                    is_active=bool(data.get("active", True)),
                )
            )
    session.commit()

    vacancy_map: dict[int, int] = {}
    for data in legacy_vacancies:
        source = normalize_source(data.get("source") or "hh")
        company = upsert_company(session, source=source, name=data.get("company") or "Не указана")
        location = upsert_location(session, source=source, name=data.get("location") or "")
        desc_short = data.get("description") or ""
        desc_full = data.get("full_description") or desc_short
        skills = []
        if data.get("skills"):
            try:
                skills = json.loads(data["skills"])
            except json.JSONDecodeError:
                pass
        vacancy = Vacancy(
            source=source,
            external_id=str(data.get("external_id") or data.get("id")),
            external_url=data.get("url") or f"{source}:{data.get('external_id')}",
            title=data.get("title") or "Без названия",
            company_id=company.id if company else None,
            description_short=desc_short,
            description_full=desc_full,
            salary_from=data.get("salary_min"),
            salary_to=data.get("salary_max"),
            salary_currency=data.get("salary_currency") or "RUR",
            salary_text=data.get("salary"),
            work_format=data.get("work_format"),
            schedule=data.get("work_schedule"),
            employment=data.get("employment"),
            location_id=location.id if location else None,
            location_text=data.get("location"),
            experience_required=data.get("experience"),
            user_status=data.get("status") or "new",
            rule_score=data.get("score") or 0,
            rule_score_reasons=data.get("score_reasons"),
            published_at=parse_datetime(data.get("published_at")),
            enriched_at=parse_datetime(data.get("enriched_at")),
        )
        session.add(vacancy)
        session.flush()
        sync_vacancy_skills(session, vacancy.id, skills if isinstance(skills, list) else [])
        vacancy_map[data["id"]] = vacancy.id
    session.commit()
    print(f"✅ Вакансии: {len(vacancy_map)}")

    for data in match_rows:
        vid = vacancy_map.get(data.get("vacancy_id"))
        pid = profile_map.get(data.get("profile_id"))
        if vid and pid:
            session.add(
                VacancyMatch(
                    vacancy_id=vid,
                    profile_id=pid,
                    match_score=float(data.get("match_score") or 0),
                    match_level=data.get("match_level") or "fast",
                    matched_skills_json=data.get("matched_skills"),
                    missing_skills_json=data.get("missing_skills"),
                    strengths_for_vacancy_json=data.get("strengths"),
                    risks_json=data.get("risks"),
                    recommendation=data.get("recommendation"),
                    ai_analysis=data.get("deep_analysis") or data.get("match_summary"),
                )
            )
    session.commit()

    for data in cache_rows:
        session.add(
            AICache(
                cache_key=data["cache_key"],
                provider=data.get("provider") or "ollama",
                task_type=data.get("task_type") or "unknown",
                response=data.get("response") or "{}",
                tokens_used=data.get("tokens_used") or 0,
                expires_at=parse_datetime(data.get("expires_at")),
            )
        )
    session.commit()

    session.close()
    print("\n🎉 Миграция завершена!")


if __name__ == "__main__":
    main()
