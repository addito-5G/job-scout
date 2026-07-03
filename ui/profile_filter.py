"""Выбор профиля поиска в сайдбаре."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.profile_filter_service import get_active_filter_role, list_profile_filters
from ui.data import cached_profile_id, clear_data_cache


def get_selected_profile_role() -> str | None:
    return st.session_state.get("selected_profile_role")


def get_selected_profile_label() -> str | None:
    return st.session_state.get("selected_profile_label")


def render_profile_filter_sidebar() -> str | None:
    profile_id = cached_profile_id()
    if profile_id is None:
        return None

    init_db()
    session = get_session()
    try:
        filters = list_profile_filters(session, profile_id)
        if not filters:
            return None

        labels = [f["label"] for f in filters]
        roles = [f["role"] for f in filters]
        active_role = get_active_filter_role(session, profile_id)

        default_role = st.session_state.get("selected_profile_role") or active_role or roles[0]
        if default_role not in roles:
            default_role = roles[0]

        default_index = roles.index(default_role)
        prev_role = st.session_state.get("selected_profile_role")

        choice = st.sidebar.selectbox(
            "Профиль поиска",
            options=labels,
            index=default_index,
            help="Фильтр вакансий и аналитики по должности из резюме",
        )
        selected_role = roles[labels.index(choice)]
        selected_label = choice
        st.session_state.selected_profile_role = selected_role
        st.session_state.selected_profile_label = selected_label

        if prev_role is not None and prev_role != selected_role:
            st.session_state.pop("resume_advice_result", None)
            st.session_state.run_resume_advice = False
            clear_data_cache()

        return selected_role
    finally:
        session.close()
