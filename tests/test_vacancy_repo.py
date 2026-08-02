"""Тесты границ слоя repository (Фаза 2)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, CandidateProfile, SearchSettings, Vacancy
from db.repositories.vacancy_repo import count_new_vacancies, upsert_vacancy
from models import Vacancy as VacancyDTO
from services.profile_filter_service import ROLE_PRODUCT_MANAGER
from services.vacancy_service import upsert_scored_vacancy
from time_utils import utc_now


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
    profile = CandidateProfile(display_name="Тест", resume_raw="x", full_name="Test")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def test_count_new_vacancies_by_scraped_at(db_session: Session, profile: CandidateProfile):
    recent = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="r1",
        title="PM",
        external_url="https://hh.ru/1",
        scraped_at=utc_now(),
        is_active=True,
    )
    old = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="o1",
        title="Old",
        external_url="https://hh.ru/2",
        scraped_at=utc_now() - timedelta(days=60),
        is_active=True,
    )
    db_session.add_all([recent, old])
    db_session.commit()

    assert count_new_vacancies(db_session, 7, profile_id=profile.id) == 1
    assert count_new_vacancies(db_session, 90, profile_id=profile.id) == 2


def test_upsert_vacancy_creates_new(db_session: Session, profile: CandidateProfile):
    dto = VacancyDTO(
        source="hh",
        external_id="x1",
        title="Product Manager",
        company="Acme",
            url="https://hh.ru/x1",
        )
    vid, outcome = upsert_vacancy(
        db_session,
        dto,
        profile_id=profile.id,
        search_settings_id=None,
        profile_role=ROLE_PRODUCT_MANAGER,
    )
    assert outcome == "new"
    row = db_session.get(Vacancy, vid)
    assert row is not None
    assert row.profile_id == profile.id
    assert row.profile_role == ROLE_PRODUCT_MANAGER


def test_upsert_vacancy_recovers_from_url_conflict(db_session: Session, profile: CandidateProfile):
    """Legacy UNIQUE(external_url): second insert with same URL must skip, not raise."""
    from sqlalchemy import text

    db_session.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS uq_vacancies_external_url ON vacancies(external_url)")
    )
    existing = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="old-id",
        title="Existing",
        external_url="https://hh.ru/vacancy/conflict",
        scraped_at=utc_now(),
        is_active=True,
    )
    db_session.add(existing)
    db_session.commit()

    dto = VacancyDTO(
        source="hh",
        external_id="new-id-same-url",
        title="Incoming",
        company="Acme",
        url="https://hh.ru/vacancy/conflict",
    )
    vid, outcome = upsert_vacancy(db_session, dto, profile_id=profile.id)
    assert outcome == "skipped"
    assert vid == existing.id


def test_upsert_vacancy_skips_existing(db_session: Session, profile: CandidateProfile):
    dto = VacancyDTO(
        source="hh",
        external_id="dup",
        title="Sales Manager",
        company="Acme",
            url="https://hh.ru/dup",
            salary="100 000",
        salary_min=100000,
    )
    vid1, outcome1 = upsert_vacancy(db_session, dto, profile_id=profile.id)
    assert outcome1 == "new"

    dto2 = VacancyDTO(
        source="hh",
        external_id="dup",
        title="Changed title",
        company="Other",
        url="https://hh.ru/dup",
        salary="120 000",
        salary_min=120000,
    )
    vid2, outcome2 = upsert_vacancy(db_session, dto2, profile_id=profile.id)
    assert vid2 == vid1
    assert outcome2 == "meta_updated"
    row = db_session.get(Vacancy, vid1)
    assert row.title == "Sales Manager"


def test_upsert_scored_vacancy_sets_role_from_settings(db_session: Session, profile: CandidateProfile):
    settings = SearchSettings(
        profile_id=profile.id,
        desired_titles_json='["Product Manager"]',
        is_active=True,
    )
    db_session.add(settings)
    db_session.commit()

    dto = VacancyDTO(
        source="habr",
        external_id="h1",
        title="PM role",
        url="https://habr.com/h1",
    )
    vid, outcome = upsert_scored_vacancy(
        db_session, dto, profile_id=profile.id, search_settings_id=settings.id
    )
    assert outcome == "new"
    row = db_session.get(Vacancy, vid)
    assert row is not None
    assert row.profile_role == ROLE_PRODUCT_MANAGER
    assert row.search_settings_id == settings.id
