#!/usr/bin/env python3
"""Загрузить резюме, сохранить профиль поиска, без немедленного парсинга."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import config
from db import get_session, init_db
from services.profile_service import parse_resume_file
from services.schedule_service import load_schedule, save_schedule
from services.search_service import (
    get_active_search_settings,
    save_search_settings,
    suggest_search_settings,
)


def main() -> None:
    resume_path = Path(config.DEFAULT_RESUME_PATH)
    if not resume_path.exists():
        print(f"❌ Резюме не найдено: {resume_path}")
        sys.exit(1)

    init_db()
    session = get_session()

    print(f"📄 Резюме: {resume_path}")
    profile, result = parse_resume_file(session, resume_path, upsert=True)
    print(f"✅ Профиль #{profile.id}: {profile.full_name} — {profile.title}")
    print(f"   AI: {result.provider}, tokens: {result.total_tokens}")

    print("🔑 Генерация ключей поиска...")
    settings = suggest_search_settings(session, profile.id, use_ai=True)
    titles = json.loads(settings.desired_titles_json or "[]")
    include = json.loads(settings.keywords_include_json or "[]")
    exclude = json.loads(settings.keywords_exclude_json or "[]")
    print(f"✅ SearchSettings #{settings.id}")
    print(f"   Должности: {titles}")
    print(f"   Ключи: {include[:6]}")
    print(f"   Исключить: {exclude[:6]}")

    schedule = load_schedule()
    schedule = save_schedule({**schedule, "enabled": True, "scan_time": "09:00", "timezone": "Europe/Moscow"})
    print(f"🕘 Расписание: {schedule['scan_time']} {schedule['timezone']} (enabled={schedule['enabled']})")

    active = get_active_search_settings(session, profile.id)
    session.close()

    print("\nГотово. Следующий автосбор — по расписанию (launchd / daily_update.py).")
    print("Проверка вручную: python scripts/daily_update.py --trigger scheduled")


if __name__ == "__main__":
    main()
