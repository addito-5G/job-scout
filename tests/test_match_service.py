"""Тесты compute_fit_match."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.entities import sync_vacancy_skills
from db.models import Base, CandidateProfile, Company, Vacancy
from services.match_service import compute_fit_match
from services.vacancy_service.match_view import match_has_analysis, pick_best_match


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def profile(db_session: Session) -> CandidateProfile:
    row = CandidateProfile(
        display_name="Test",
        resume_raw="cv",
        title="Product Manager",
        experience_years=15,
        skills_json=json.dumps(["Product Manager", "SQL", "Python", "Growth"], ensure_ascii=False),
        strengths_json=json.dumps(["Запуск B2B SaaS"], ensure_ascii=False),
    )
    db_session.add(row)
    db_session.commit()
    return row


def test_compute_fit_match_persists_score(db_session: Session, profile: CandidateProfile):
    company = Company(name="UZUM", source="hh", external_id="uzum")
    db_session.add(company)
    db_session.flush()

    vacancy = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="uzum-1",
        external_url="https://hh.ru/vacancy/uzum-1",
        title="Middle+ Product Manager (Growth)",
        company_id=company.id,
        description_short="SQL, Python, growth, unit economics",
        description_full="Product Manager для growth. SQL, Python, A/B, retention, discovery.",
        experience_required="От 3 до 6 лет",
        is_active=True,
    )
    db_session.add(vacancy)
    db_session.commit()

    sync_vacancy_skills(
        db_session,
        vacancy.id,
        ["Product Manager", "SQL", "Python", "Growth"],
    )

    data = compute_fit_match(db_session, profile, vacancy)
    assert data["match_score"] > 0
    assert data["recommendation"] in ("apply", "improve_resume")
    assert data["matched_skills"]


def test_pick_best_match_prefers_fit_dict():
    fit = {"match_score": 80, "matched_skills": ["SQL"], "match_summary": "ok"}
    legacy = {"match_score": 60, "matched_skills": ["x"]}
    assert pick_best_match(fit, legacy) is fit


def test_match_has_analysis_with_gaps():
    match = {
        "match_score": 65,
        "matched_skills": ["SQL"],
        "missing_skills": ["UX"],
        "match_summary": "summary",
    }
    assert match_has_analysis(match)
