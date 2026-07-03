"""Тесты доменной логики ролей."""

from __future__ import annotations

from domain.role import (
    ROLE_GENERAL,
    ROLE_PRODUCT_ANALYST,
    ROLE_PRODUCT_MANAGER,
    infer_role_from_title,
    infer_target_role,
)


def test_infer_role_from_title_pm():
    assert infer_role_from_title("Product Manager") == ROLE_PRODUCT_MANAGER


def test_infer_role_from_title_analyst():
    assert infer_role_from_title("Продуктовый аналитик") == ROLE_PRODUCT_ANALYST


def test_infer_role_from_title_unknown():
    assert infer_role_from_title("Backend Developer") == "backend_developer"


def test_infer_target_role_pm_abbreviation():
    assert infer_target_role("Senior PM (B2B)") == ROLE_PRODUCT_MANAGER


def test_infer_target_role_general():
    assert infer_target_role("Backend Developer") == ROLE_GENERAL


def test_infer_target_role_normalizes_yo():
    assert infer_target_role("Продуктовый менеджер") == ROLE_PRODUCT_MANAGER
