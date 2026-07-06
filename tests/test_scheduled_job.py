"""Тесты scheduled_job — импорты и ранний выход без резюме."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, CandidateProfile
from services.scheduled_job import run_scheduled_update


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


def test_run_scheduled_update_without_resume_returns_early(db_session: Session):
    profile = CandidateProfile(display_name="Empty", is_active=True)
    db_session.add(profile)
    db_session.commit()

    result = run_scheduled_update(session=db_session, trigger="test")
    assert result.status == "failed"
    assert any("резюме" in e.lower() for e in result.errors)


def test_scheduled_job_imports_get_active_profile():
    import services.scheduled_job as mod

    assert callable(mod.get_active_profile)
