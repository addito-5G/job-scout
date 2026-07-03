"""Smoke-тесты detail facade."""

from __future__ import annotations

import services.detail_facade as facade


def test_detail_facade_exports():
    assert callable(facade.load_detail)
    assert callable(facade.run_fast_match)
    assert callable(facade.generate_letter)
    assert callable(facade.normalize_letter)
