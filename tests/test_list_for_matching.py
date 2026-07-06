"""Тесты выборки вакансий для fit-матчинга."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, CandidateProfile, Vacancy, VacancyMatch
from db.repositories.vacancy_repo import list_for_matching


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


def test_list_for_matching_scoped_to_profile(db_session: Session):
    profile_a = CandidateProfile(display_name="A", resume_raw="cv")
    profile_b = CandidateProfile(display_name="B", resume_raw="cv")
    db_session.add_all([profile_a, profile_b])
    db_session.commit()

    vac_a = Vacancy(
        profile_id=profile_a.id,
        source="hh",
        external_id="a1",
        title="Sales A",
        external_url="https://hh.ru/a1",
        is_active=True,
    )
    vac_b = Vacancy(
        profile_id=profile_b.id,
        source="hh",
        external_id="b1",
        title="Sales B",
        external_url="https://hh.ru/b1",
        is_active=True,
    )
    db_session.add_all([vac_a, vac_b])
    db_session.commit()

    rows = list_for_matching(db_session, profile_a.id, limit=10)
    assert len(rows) == 1
    assert rows[0].id == vac_a.id


def test_list_for_matching_prioritizes_scan_ids(db_session: Session):
    profile = CandidateProfile(display_name="P", resume_raw="cv")
    db_session.add(profile)
    db_session.commit()

    first = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="first",
        title="First",
        external_url="https://hh.ru/first",
        is_active=True,
    )
    second = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="second",
        title="Second",
        external_url="https://hh.ru/second",
        is_active=True,
    )
    db_session.add_all([first, second])
    db_session.commit()

    rows = list_for_matching(
        db_session,
        profile.id,
        limit=1,
        priority_vacancy_ids=[second.id, first.id],
    )
    assert len(rows) == 1
    assert rows[0].id == second.id


def test_list_for_matching_skips_already_matched(db_session: Session):
    profile = CandidateProfile(display_name="P", resume_raw="cv")
    db_session.add(profile)
    db_session.commit()

    vac = Vacancy(
        profile_id=profile.id,
        source="hh",
        external_id="x",
        title="PM",
        external_url="https://hh.ru/x",
        is_active=True,
    )
    db_session.add(vac)
    db_session.commit()

    db_session.add(
        VacancyMatch(
            vacancy_id=vac.id,
            profile_id=profile.id,
            match_level="fit",
            match_score=60,
        )
    )
    db_session.commit()

    rows = list_for_matching(db_session, profile.id, limit=10)
    assert rows == []
