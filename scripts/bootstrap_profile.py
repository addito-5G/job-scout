#!/usr/bin/env python3
"""Загрузить резюме, сохранить профиль поиска, без немедленного парсинга."""

from __future__ import annotations

import sys
from pathlib import Path

import config
from cli_logging import setup_cli_logging
from db import get_session, init_db
from services.profile_service import parse_resume_file
from services.profile_serialization import loads_json
from services.schedule_service import load_schedule, save_schedule
from services.search_service import (
    get_active_search_settings,
    save_search_settings,
    suggest_search_settings,
)


logger = setup_cli_logging()


def main() -> None:
    resume_path = Path(config.DEFAULT_RESUME_PATH)
    if not resume_path.exists():
        logger.error(f"❌ Резюме не найдено: {resume_path}")
        sys.exit(1)

    init_db()
    session = get_session()

    logger.info(f"📄 Резюме: {resume_path}")
    profile, result = parse_resume_file(session, resume_path, upsert=True)
    logger.info(f"✅ Профиль #{profile.id}: {profile.full_name} — {profile.title}")
    logger.info(f"   AI: {result.provider}, tokens: {result.total_tokens}")

    logger.info("🔑 Генерация ключей поиска...")
    settings = suggest_search_settings(session, profile.id, use_ai=True)
    titles = loads_json(settings.desired_titles_json, [])
    include = loads_json(settings.keywords_include_json, [])
    exclude = loads_json(settings.keywords_exclude_json, [])
    logger.info(f"✅ SearchSettings #{settings.id}")
    logger.info(f"   Должности: {titles}")
    logger.info(f"   Ключи: {include[:6]}")
    logger.info(f"   Исключить: {exclude[:6]}")

    schedule = load_schedule()
    schedule = save_schedule({**schedule, "enabled": True, "scan_time": "09:00", "timezone": "Europe/Moscow"})
    logger.info(f"🕘 Расписание: {schedule['scan_time']} {schedule['timezone']} (enabled={schedule['enabled']})")

    active = get_active_search_settings(session, profile.id)
    session.close()

    logger.info("\nГотово. Следующий автосбор — по расписанию (launchd / daily_update.py).")
    logger.info("Проверка вручную: python scripts/daily_update.py --trigger scheduled")


if __name__ == "__main__":
    main()
