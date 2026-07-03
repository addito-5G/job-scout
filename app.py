#!/usr/bin/env python3
"""NextMove — AI Career Copilot (Streamlit UI)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from db import get_session, init_db
from services.profile_service import get_latest_profile
from services.search_service import get_active_search_settings
from ui.applications_page import render_applications
from ui.brand import PRODUCT_NAME, PRODUCT_TAGLINE
from ui.design_system import inject_design_system
from ui.detail_page import render_detail
from ui.extract_progress import run_extract_with_progress
from ui.market_insights_page import render_market_insights
from ui.navigation import render_app_sidebar, render_setup_sidebar
from ui.onboarding_page import render_onboarding
from ui.opportunities_page import render_opportunities
from ui.parse_progress import run_parse_with_progress
from ui.parse_setup_page import render_keywords_step
from ui.resume_advice_page import render_resume_advice
from ui.today_page import render_today
from ui.workflow import render_stepper, resolve_initial_stage


st.set_page_config(
    page_title=PRODUCT_NAME,
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_design_system()


def _bootstrap() -> tuple[bool, bool]:
    init_db()
    session = get_session()
    try:
        profile = get_latest_profile(session)
        has_resume = bool(profile and profile.resume_raw)
        has_settings = bool(
            profile and get_active_search_settings(session, profile.id)
        )
        return has_resume, has_settings
    finally:
        session.close()


def main() -> None:
    st.session_state.setdefault("view", "today")
    st.session_state.setdefault("selected_source", "hh")

    vacancy_id = st.query_params.get("vacancy_id")
    if vacancy_id and not st.session_state.get("refresh_running"):
        try:
            st.session_state.view = "detail"
            st.session_state.selected_vacancy_id = int(vacancy_id)
            st.session_state.workflow_stage = "app"
            st.session_state.app_unlocked = True
        except ValueError:
            pass

    has_resume, has_settings = _bootstrap()
    stage = resolve_initial_stage(has_resume=has_resume, has_settings=has_settings)

    if st.session_state.get("extract_running"):
        stage = "extracting"
    if st.session_state.get("refresh_running"):
        stage = "parsing"

    if stage == "parsing":
        render_setup_sidebar()
        run_parse_with_progress()
        return

    if stage != "app" and not (has_settings and st.session_state.get("view") == "setup"):
        render_setup_sidebar()
        render_stepper(stage)

        if stage == "input":
            render_onboarding()
            return

        if stage == "extracting":
            st.sidebar.caption("Идёт анализ резюме…")
            run_extract_with_progress()
            return

        if stage == "keywords":
            render_keywords_step(setup_mode=False)
            return

    if st.session_state.get("view") == "setup":
        render_setup_sidebar()
        render_keywords_step(setup_mode=True)
        return

    st.session_state.app_unlocked = True
    render_app_sidebar(has_resume=has_resume)

    view = st.session_state.view
    if view == "today":
        render_today()
    elif view in ("opportunities", "vacancies"):
        render_opportunities()
    elif view == "saved":
        render_opportunities(saved_only=True)
    elif view == "resume" or view == "resume_advice":
        st.markdown(
            '<div class="nm-eyebrow">Резюме</div>'
            '<div class="nm-title" style="font-size:1.35rem">Усильте резюме</div>'
            '<p class="nm-subtitle">AI Resume Coach — что добавить, чтобы поднять match</p>',
            unsafe_allow_html=True,
        )
        render_resume_advice()
    elif view == "applications":
        render_applications()
    elif view == "insights" or view == "dashboard":
        render_market_insights()
    elif view == "detail":
        vid = st.session_state.get("selected_vacancy_id")
        if vid:
            render_detail(vid)
        else:
            st.session_state.view = "opportunities"
            st.rerun()
    else:
        st.session_state.view = "today"
        render_today()


if __name__ == "__main__":
    main()
