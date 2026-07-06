"""Тесты detail facade."""

from __future__ import annotations

from services import detail_facade as facade


def test_facade_exports_fit_refresh():
    assert callable(facade.refresh_fit_match)
    assert callable(facade.best_match)
