"""Тесты группировки вакансий по компаниям."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, CandidateProfile, Company, Vacancy
from services.vacancy_service import VacancyFilters, list_companies, list_vacancies


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


def test_list_companies_groups_vacancies(db_session: Session):
    profile = CandidateProfile(display_name="P", resume_raw="cv", is_active=True)
    db_session.add(profile)
    db_session.commit()

    company = Company(external_id="c1", source="hh", name="СДЭК Бизнес Пост")
    db_session.add(company)
    db_session.commit()

    for i in range(3):
        db_session.add(
            Vacancy(
                profile_id=profile.id,
                company_id=company.id,
                source="hh",
                external_id=f"v{i}",
                title=f"Менеджер {i}",
                external_url=f"https://hh.ru/{i}",
                is_active=True,
            )
        )
    db_session.commit()

    items, total = list_companies(
        db_session,
        profile.id,
        VacancyFilters(page=1, per_page=20),
    )
    assert total == 1
    assert len(items) == 1
    assert items[0].name == "СДЭК Бизнес Пост"
    assert items[0].vacancy_count == 3


def test_list_vacancies_filters_by_company(db_session: Session):
    profile = CandidateProfile(display_name="P", resume_raw="cv")
    c1 = Company(external_id="a", source="hh", name="A")
    c2 = Company(external_id="b", source="hh", name="B")
    db_session.add_all([profile, c1, c2])
    db_session.commit()

    db_session.add_all(
        [
            Vacancy(
                profile_id=profile.id,
                company_id=c1.id,
                source="hh",
                external_id="1",
                title="Role A",
                external_url="https://hh.ru/1",
                is_active=True,
            ),
            Vacancy(
                profile_id=profile.id,
                company_id=c2.id,
                source="hh",
                external_id="2",
                title="Role B",
                external_url="https://hh.ru/2",
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    items, total = list_vacancies(
        db_session,
        profile.id,
        VacancyFilters(company_id=c1.id, page=1, per_page=20),
    )
    assert total == 1
    assert items[0].title == "Role A"
