"""Выбор профиля резюме в сайдбаре."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.profile_service import get_active_profile, list_profiles, set_active_profile
from ui.data import clear_data_cache
from ui.workflow import start_resume_upload


def get_active_resume_profile_id() -> int | None:
    return st.session_state.get("active_resume_profile_id")


def get_active_resume_profile_label() -> str | None:
    return st.session_state.get("active_resume_profile_label")


def render_profile_filter_sidebar() -> int | None:
    init_db()
    session = get_session()
    try:
        profiles = list_profiles(session)
        if not profiles:
            return None

        labels = [p.display_name for p in profiles]
        ids = [p.id for p in profiles]
        active = get_active_profile(session)
        default_id = st.session_state.get("active_resume_profile_id") or (active.id if active else ids[0])
        if default_id not in ids:
            default_id = ids[0]

        prev_id = st.session_state.get("active_resume_profile_id")
        default_index = ids.index(default_id)

        choice = st.sidebar.selectbox(
            "Профиль резюме",
            options=labels,
            index=default_index,
            help="Весь интерфейс и база вакансий привязаны к выбранному профилю резюме.",
        )
        selected_id = ids[labels.index(choice)]
        selected_label = choice
        st.session_state.active_resume_profile_id = selected_id
        st.session_state.active_resume_profile_label = selected_label

        if prev_id is not None and prev_id != selected_id:
            set_active_profile(session, selected_id)
            st.session_state.pop("resume_advice_result", None)
            st.session_state.run_resume_advice = False
            clear_data_cache()
        elif active and active.id != selected_id:
            set_active_profile(session, selected_id)

        return selected_id
    finally:
        session.close()


def render_resume_upload_sidebar() -> None:
    if st.sidebar.button(
        "📎 Загрузить новое резюме",
        use_container_width=True,
        help="Создать новый изолированный профиль с отдельной базой вакансий",
    ):
        start_resume_upload()
        st.rerun()
