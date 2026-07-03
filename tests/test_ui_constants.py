"""Тесты UI-констант (Фаза 3)."""

from __future__ import annotations

from ui.constants import recommendation_label


def test_recommendation_label_full():
    assert "Откликаться" in recommendation_label("apply")


def test_recommendation_label_short():
    assert recommendation_label("apply", short=True) == "Откликаться"


def test_recommendation_label_unknown_passthrough():
    assert recommendation_label("custom") == "custom"
