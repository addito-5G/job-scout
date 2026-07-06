"""Smoke-тесты config_loader."""

from __future__ import annotations

from config_loader import load_criteria, load_criteria_with_browser, load_sources


def test_load_criteria_has_profile():
    data = load_criteria()
    assert "profile" in data
    assert data["profile"].get("title")


def test_load_sources_has_browser_key():
    data = load_sources()
    assert "browser" in data or "sources" in data


def test_load_criteria_with_browser_merges_browser():
    data = load_criteria_with_browser()
    assert "browser" in data
    assert "profile" in data
