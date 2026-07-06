#!/usr/bin/env python3
"""Расчёт соответствия вакансий профилю кандидата."""

from __future__ import annotations

import argparse
import json

from cli_logging import setup_cli_logging
from db import get_session, init_db
from db.repositories.vacancy_repo import get_vacancy_by_id
from services.match_service import batch_fit_match, compute_fit_match
from services.profile_service import get_latest_profile

logger = setup_cli_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Scout — fit matching")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--profile-id", type=int, default=None)
    parser.add_argument("--vacancy-id", type=int, default=None, help="Fit score для одной вакансии")
    args = parser.parse_args()

    init_db()
    session = get_session()

    if args.vacancy_id:
        profile = get_latest_profile(session)
        vacancy = get_vacancy_by_id(session, args.vacancy_id)
        if not profile or not vacancy:
            print("Профиль или вакансия не найдены")
            return
        print(f"→ Fit score #{vacancy.id} с профилем #{profile.id}...")
        data = compute_fit_match(session, profile, vacancy)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        session.close()
        return

    print(f"→ Batch fit match (limit={args.limit})...")
    matched, errors = batch_fit_match(session, profile_id=args.profile_id, limit=args.limit)
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
                WHERE m.profile_id = :pid AND m.match_level = 'fit'
                ORDER BY m.match_score DESC LIMIT 5
                """
            ),
            {"pid": profile.id},
        ).fetchall()
        if top:
            print("\nТоп-5 по fit score:")
            for row in top:
                print(f"  [{int(row[1])}%] {row[0]} — {row[2]}")

    session.close()


if __name__ == "__main__":
    main()
