"""Тесты resolve_initial_stage."""

from __future__ import annotations

import streamlit as st

from ui.workflow import resolve_initial_stage


def test_resolve_initial_stage_honors_input_after_existing_profile(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    st.session_state["workflow_stage"] = "input"
    assert resolve_initial_stage(has_resume=True, has_settings=True) == "input"


def test_resolve_initial_stage_app_when_ready(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    st.session_state["workflow_stage"] = "app"
    assert resolve_initial_stage(has_resume=True, has_settings=True) == "app"
