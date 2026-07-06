"""Тесты CLI review (session lifecycle)."""

from __future__ import annotations

import importlib.util
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

REVIEW_PATH = Path(__file__).resolve().parent.parent / "scripts" / "review.py"


def _load_review():
    spec = importlib.util.spec_from_file_location("review_cli", REVIEW_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cmd_show_loads_skills_before_session_close():
    review = _load_review()
    vacancy = MagicMock()
    vacancy.id = 1
    vacancy.title = "PM"
    vacancy.company_rel = None
    vacancy.external_url = "https://example.com"
    vacancy.salary_text = ""
    vacancy.employment = ""
    vacancy.schedule = ""
    vacancy.experience_required = ""
    vacancy.description_full = "desc"
    vacancy.description_short = ""

    session = MagicMock()

    with (
        patch.object(review, "get_session", return_value=session),
        patch.object(review, "get_vacancy_by_id", return_value=vacancy) as get_row,
        patch.object(review, "get_vacancy_skills", return_value=["Python", "SQL"]) as get_skills,
    ):
        review.cmd_show(Namespace(id=1))

    get_row.assert_called_once_with(session, 1)
    get_skills.assert_called_once_with(session, 1)
    session.close.assert_called_once()
