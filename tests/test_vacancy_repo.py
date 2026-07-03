"""Тесты границ слоя repository (Фаза 2)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Vacancy
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


def test_count_new_vacancies_by_scraped_at(db_session: Session):
    recent = Vacancy(
        source="hh",
        external_id="r1",
        title="PM",
        external_url="https://hh.ru/1",
        scraped_at=utc_now(),
        is_active=True,
    )
    old = Vacancy(
        source="hh",
        external_id="o1",
        title="Old",
        external_url="https://hh.ru/2",
        scraped_at=utc_now() - timedelta(days=60),
        is_active=True,
    )
    db_session.add_all([recent, old])
    db_session.commit()

    assert count_new_vacancies(db_session, 7) == 1
    assert count_new_vacancies(db_session, 90) == 2


def test_upsert_vacancy_accepts_profile_role(db_session: Session):
    dto = VacancyDTO(
        source="hh",
        external_id="x1",
        title="Product Manager",
        company="Acme",
        url="https://hh.ru/x1",
        score=50,
    )
    vid, is_new = upsert_vacancy(
        db_session,
        dto,
        search_settings_id=None,
        profile_role=ROLE_PRODUCT_MANAGER,
    )
    assert is_new is True
    row = db_session.get(Vacancy, vid)
    assert row is not None
    assert row.profile_role == ROLE_PRODUCT_MANAGER


def test_upsert_scored_vacancy_sets_role_from_settings(db_session: Session):
    from db.models import CandidateProfile, SearchSettings

    profile = CandidateProfile(resume_raw="x", full_name="Test")
    db_session.add(profile)
    db_session.flush()
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
        score=40,
    )
    vid, _ = upsert_scored_vacancy(db_session, dto, search_settings_id=settings.id)
    row = db_session.get(Vacancy, vid)
    assert row is not None
    assert row.profile_role == ROLE_PRODUCT_MANAGER
    assert row.search_settings_id == settings.id
