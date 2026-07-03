#!/usr/bin/env python3
"""Тест AI-профилирования резюме из Obsidian."""

from __future__ import annotations

import argparse
import json


import config
from services.profile_serialization import loads_json
from ai import AIRouter
from db import get_session, init_db
from services.profile_service import get_latest_profile, parse_resume_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse resume via AI router")
    parser.add_argument(
        "--resume",
        default=config.DEFAULT_RESUME_PATH,
        help="Path to resume .md",
    )
    parser.add_argument("--clear-cache", action="store_true", help="Clear AI cache before run")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache for this run")
    args = parser.parse_args()

    init_db()
    session = get_session()
    router = AIRouter(session)

    if args.clear_cache:
        deleted = router.clear_cache()
        print(f"🗑️  Cache cleared: {deleted} entries")

    print(f"📄 Resume: {args.resume}")
    print("⏳ Parsing (Ollama + Yandex)...")

    profile, result = parse_resume_file(session, args.resume, upsert=True)

    print("\n" + "=" * 60)
    print(f"✅ Profile saved: id={profile.id}")
    print(f"   Name:    {profile.full_name}")
    print(f"   Title:   {profile.title}")
    print(f"   Exp:     {profile.experience_years} лет")
    print(f"   Salary:  {profile.salary_min}–{profile.salary_max} {profile.salary_currency}")
    print(f"   AI:      {profile.ai_summary[:120]}..." if profile.ai_summary else "")
    print(f"   Provider: {result.provider} ({result.model})")
    print(f"   Tokens:  {result.total_tokens}")

    if result.warnings:
        print("\n⚠️  Usage warnings:")
        for w in result.warnings:
            print(f"   {w}")

    print("\n📊 Usage summary:")
    print(json.dumps(router.usage_summary(), ensure_ascii=False, indent=2))

    print("\n📋 Cache stats:", router.cache.stats())

    skills = loads_json(profile.skills_json, [])
    strengths = loads_json(profile.strengths_json, [])
    print(f"\nSkills ({len(skills)}): {', '.join(skills[:8])}...")
    print(f"Strengths: {strengths[:3]}")

    latest = get_latest_profile(session)
    print(f"\nLatest profile in DB: #{latest.id if latest else 'none'}")
    session.close()


if __name__ == "__main__":
    main()
