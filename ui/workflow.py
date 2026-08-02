"""Пошаговый сценарий Job Scout."""

from __future__ import annotations

import streamlit as st

STAGES = ("input", "extracting", "keywords", "parsing", "app")

STAGE_LABELS = {
    "input": "1. Резюме",
    "extracting": "2. Извлечение ключей",
    "keywords": "3. Настройка ключей",
    "parsing": "4. Обновление",
    "app": "5. Работа",
}


def render_stepper(current: str) -> None:
    if current in ("app", "setup"):
        return
    cols = st.columns(3)
    wizard = ("input", "extracting", "keywords")
    labels = {
        "input": "1. Резюме",
        "extracting": "2. Ключи",
        "keywords": "3. Профиль",
    }
    order = list(wizard)
    cur_idx = order.index(current) if current in order else 0
    for col, stage in zip(cols, wizard):
        idx = order.index(stage)
        if idx < cur_idx:
            col.success(f"✓ {labels[stage]}")
        elif idx == cur_idx:
            col.info(f"→ {labels[stage]}")
        else:
            col.caption(labels[stage])


def go_to(stage: str) -> None:
    if stage in STAGES:
        st.session_state.workflow_stage = stage


def go_to_setup() -> None:
    st.session_state.view = "setup"
    st.session_state.workflow_stage = "keywords"


def go_to_work() -> None:
    st.session_state.view = "today"
    st.session_state.workflow_stage = "app"


def reset_to_input() -> None:
    st.session_state.workflow_stage = "input"
    st.session_state.view = "today"
    st.session_state.app_unlocked = False
    st.session_state.keys_extracted = False
    st.session_state.pop("search_draft", None)
    st.session_state.pop("resume_paste", None)
    st.session_state.pop("onboard_file", None)
    st.session_state.pop("pending_resume_bytes", None)
    st.session_state.pop("processed_resume_id", None)
    for key in list(st.session_state.keys()):
        if key.startswith("kw_") or key.startswith("add_") or key.startswith("del_"):
            del st.session_state[key]


def start_resume_upload() -> None:
    """Вернуться к экрану загрузки резюме."""
    reset_to_input()


def start_manual_refresh() -> None:
    from services.parse_estimate import estimate_parse_seconds

    st.session_state.refresh_running = True
    st.session_state.parse_eta_seconds = estimate_parse_seconds()
    st.session_state.parse_started_at = __import__("time").time()
    go_to("parsing")


def resolve_initial_stage(*, has_resume: bool, has_settings: bool) -> str:
    if st.session_state.get("refresh_running"):
        return "parsing"
    if st.session_state.get("extract_running"):
        return "extracting"
    if st.session_state.get("view") == "setup":
        return "keywords"

    explicit = st.session_state.get("workflow_stage")
    if explicit == "input":
        return "input"
    if explicit == "keywords" and not has_settings:
        return "keywords"
    if has_resume and has_settings and explicit not in ("input", "extracting", "keywords"):
        return "app"
    if explicit:
        return explicit
    if has_resume and st.session_state.get("keys_extracted"):
        return "keywords"
    return "input"
