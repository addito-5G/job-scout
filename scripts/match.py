#!/usr/bin/env python3
"""AI-матчинг вакансий с профилем кандидата."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from db import get_session, init_db
from services.match_service import batch_fast_match, deep_match_vacancy
from services.profile_service import get_latest_profile
from db.repositories.vacancy_repo import get_vacancy_by_id

logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_criteria() -> dict:
    with (ROOT / "config" / "criteria.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — AI matching")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-score", type=int, default=None)
    parser.add_argument("--profile-id", type=int, default=None)
    parser.add_argument("--vacancy-id", type=int, default=None, help="Deep match для одной вакансии")
    args = parser.parse_args()

    criteria = load_criteria()
    min_score = args.min_score
    if min_score is None:
        min_score = int(criteria.get("thresholds", {}).get("min_score", 0))

    init_db()
    session = get_session()

    if args.vacancy_id:
        profile = get_latest_profile(session)
        vacancy = get_vacancy_by_id(session, args.vacancy_id)
        if not profile or not vacancy:
            print("Профиль или вакансия не найдены")
            return
        print(f"→ Deep match #{vacancy.id} с профилем #{profile.id}...")
        data = deep_match_vacancy(session, profile, vacancy)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        session.close()
        return

    print(f"→ Fast match (limit={args.limit}, min_score={min_score})...")
    matched, errors = batch_fast_match(
        session, profile_id=args.profile_id, limit=args.limit, min_score=min_score
    )
    print(f"\nГотово: {matched} вакансий, ошибок {len(errors)}")
    if errors:
        for e in errors[:5]:
            print(f"  - {e}")

    profile = get_latest_profile(session)
    if profile:
        top = session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT v.title, m.match_score, m.recommendation
                FROM vacancy_matches m
                JOIN vacancies v ON v.id = m.vacancy_id
                WHERE m.profile_id = :pid AND m.match_level = 'fast'
                ORDER BY m.match_score DESC LIMIT 5
                """
            ),
            {"pid": profile.id},
        ).fetchall()
        if top:
            print("\nТоп-5 по match_score:")
            for row in top:
                print(f"  [{row[1]}%] {row[0]} — {row[2]}")

    session.close()


if __name__ == "__main__":
    main()
