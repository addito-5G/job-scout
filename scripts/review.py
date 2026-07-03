#!/usr/bin/env python3
"""Просмотр очереди и генерация сопроводительных (CLI)."""

from __future__ import annotations

import argparse


from config_loader import load_criteria
from db import get_session, init_db
from db.repositories.vacancy_repo import get_vacancy_by_id, get_vacancy_skills
from services.cover_letter_service import generate_cover_letter
from services.profile_service import get_latest_profile
from services.vacancy_service import list_for_review, update_vacancy_status


def cmd_list(args: argparse.Namespace) -> None:
    criteria = load_criteria()
    priority = criteria.get("thresholds", {}).get("priority_score", 70)
    session = get_session()
    rows = list_for_review(session, min_score=args.min_score, status=args.status, limit=args.limit)
    session.close()

    if not rows:
        print("Очередь пуста. Запустите: python scripts/scan.py")
        return

    print(f"{'ID':>4}  {'Sc':>3}  {'St':8}  Заголовок")
    print("-" * 72)
    for r in rows:
        mark = "★" if r.rule_score >= priority else " "
        print(f"{mark}{r.id:>3}  {r.rule_score:>3}  {r.user_status:8}  {r.title[:50]}")
        company = r.company_rel.name if r.company_rel else "—"
        print(f"      {company} | {r.external_url}")


def cmd_show(args: argparse.Namespace) -> None:
    session = get_session()
    row = get_vacancy_by_id(session, args.id)
    if not row:
        session.close()
        print("Не найдено")
        return
    skills = get_vacancy_skills(session, row.id)
    session.close()

    print(f"# {row.title}\n")
    print(f"Компания: {row.company_rel.name if row.company_rel else '—'}")
    print(f"Score: {row.rule_score} ({row.rule_score_reasons})")
    print(f"URL: {row.external_url}")
    if row.salary_text:
        print(f"ЗП: {row.salary_text}")
    if row.employment:
        print(f"Занятость: {row.employment} · {row.schedule or ''} · {row.experience_required or ''}")
    if skills:
        print(f"Навыки: {', '.join(skills)}")
    print()
    text = row.description_full or row.description_short or ""
    print(text[:3000] if text else "(нет описания)")


def cmd_letter(args: argparse.Namespace) -> None:
    session = get_session()
    profile = get_latest_profile(session)
    vacancy = get_vacancy_by_id(session, args.id)
    if not profile or not vacancy:
        session.close()
        print("Профиль или вакансия не найдены")
        return
    letter = generate_cover_letter(session, profile, vacancy)
    session.close()
    print(letter)
    print("\n---")
    print("Скопируйте на площадку. После отклика: python scripts/review.py applied", args.id)


def cmd_applied(args: argparse.Namespace) -> None:
    session = get_session()
    update_vacancy_status(session, args.id, "applied")
    session.close()
    print(f"#{args.id} → applied")


def cmd_skip(args: argparse.Namespace) -> None:
    session = get_session()
    update_vacancy_status(session, args.id, "skipped")
    session.close()
    print(f"#{args.id} → skipped")


def main() -> None:
    init_db()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Список вакансий")
    p_list.add_argument("--min-score", type=int, default=55)
    p_list.add_argument("--status", default=None)
    p_list.add_argument("--limit", type=int, default=30)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Детали вакансии")
    p_show.add_argument("id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_letter = sub.add_parser("letter", help="Сопроводительное письмо")
    p_letter.add_argument("id", type=int)
    p_letter.set_defaults(func=cmd_letter)

    p_applied = sub.add_parser("applied", help="Отметить отклик отправленным")
    p_applied.add_argument("id", type=int)
    p_applied.set_defaults(func=cmd_applied)

    p_skip = sub.add_parser("skip", help="Пропустить")
    p_skip.add_argument("id", type=int)
    p_skip.set_defaults(func=cmd_skip)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
