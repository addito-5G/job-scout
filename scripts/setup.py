#!/usr/bin/env python3
"""Полная настройка: миграция БД → профиль → настройки поиска."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import config
from db import get_session, init_db
from services.profile_service import get_latest_profile, parse_resume_file
from services.search_service import get_active_search_settings, settings_to_queries, suggest_search_settings


def main() -> None:
    init_db()
    session = get_session()

    print("=" * 60)
    print("JOB SCOUT — SETUP ЭТАП 1")
    print("=" * 60)

    # 1. Миграция вакансий
    print("\n[1/3] Миграция вакансий...")
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts" / "migrate_vacancies.py")], check=True)

    # 2. Профиль
    print("\n[2/3] Парсинг резюме...")
    resume_path = config.DEFAULT_RESUME_PATH
    existing = get_latest_profile(session)
    if existing:
        label = existing.full_name or f"#{existing.id}"
        answer = input(
            f"Профиль уже есть ({label}). Обновить существующий профиль? (y/n): "
        ).strip().lower()
        if answer in ("y", "yes", "д", "да"):
            profile, result = parse_resume_file(session, resume_path, upsert=True)
            print(f"✅ Profile #{profile.id} обновлён: {profile.full_name} — {profile.title}")
            print(f"   Provider: {result.provider}, tokens: {result.total_tokens}")
        else:
            profile = existing
            print(f"⏭️  Используем существующий профиль #{profile.id}: {profile.full_name} — {profile.title}")
    else:
        profile, result = parse_resume_file(session, resume_path, upsert=True)
        print(f"✅ Profile #{profile.id}: {profile.full_name} — {profile.title}")
        print(f"   Provider: {result.provider}, tokens: {result.total_tokens}")

    # 3. Настройки поиска
    print("\n[3/3] Генерация настроек поиска (AI)...")
    settings = suggest_search_settings(session, profile.id)
    queries = settings_to_queries(settings)

    print(f"✅ SearchSettings #{settings.id}")
    print(f"   Titles: {json.loads(settings.desired_titles_json or '[]')}")
    print(f"   Salary: {settings.salary_min}–{settings.salary_max} {settings.salary_currency}")
    print(f"   Include: {json.loads(settings.keywords_include_json or '[]')[:5]}")
    print(f"   Exclude: {json.loads(settings.keywords_exclude_json or '[]')}")
    print(f"\n   HH queries ({len(queries)}):")
    for q in queries:
        print(f"     - {q}")

    active = get_active_search_settings(session, profile.id)
    print(f"\n   Active settings id: {active.id if active else 'none'}")
    session.close()
    print("\n" + "=" * 60)
    print("Готово. Следующий шаг: python scripts/scan.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
