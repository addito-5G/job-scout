"""Goal-oriented navigation — user intent, not implementation."""

from __future__ import annotations

import streamlit as st

from ui.data import cached_last_scan, cached_schedule_summary
from ui.design_system import render_sidebar_brand
from ui.profile_filter import render_profile_filter_sidebar, render_resume_upload_sidebar
from ui.workflow import go_to_setup, start_manual_refresh

SOURCE_META: dict[str, tuple[str, str]] = {
    "hh": ("HeadHunter", "🟥"),
    "habr": ("Habr Career", "🟦"),
    "geekjob": ("Geekjob", "🟩"),
    "linkedin": ("LinkedIn", "🔗"),
}

NAV_ITEMS: list[tuple[str, str, str]] = [
    ("today", "🏠", "Сегодня"),
    ("opportunities", "🎯", "Возможности"),
    ("saved", "⭐", "Сохранённые"),
    ("resume", "📄", "Резюме"),
    ("applications", "✉", "Отклики"),
    ("insights", "📈", "Рынок"),
]


def _go_view(view: str) -> None:
    st.session_state.view = view
    if view != "detail":
        st.query_params.clear()
    st.rerun()


def _render_scan_status() -> None:
    st.sidebar.markdown(
        '<div class="nm-section-label" style="margin-top:0">Сканирование рынка</div>',
        unsafe_allow_html=True,
    )
    summary = cached_schedule_summary()
    last = cached_last_scan()

    if last:
        st.sidebar.caption(f"Последний сбор: **{last['finished_at']}**")
        st.sidebar.caption(f"+{last['new_added']} новых · {last['total_found']} всего")
    else:
        st.sidebar.warning("Рынок ещё не просканирован")

    if summary["enabled"]:
        st.sidebar.caption(f"Авто: **{summary['scan_time']}** МСК · след. {summary['next_run']}")

    if st.sidebar.button("🔄 Сканировать рынок", use_container_width=True, type="primary"):
        start_manual_refresh()
        st.rerun()

    st.sidebar.divider()


def render_app_sidebar(*, has_resume: bool) -> None:
    render_sidebar_brand()
    _render_scan_status()
    render_profile_filter_sidebar()
    render_resume_upload_sidebar()

    current = st.session_state.get("view", "today")
    st.sidebar.markdown(
        '<div class="nm-section-label">Навигация</div>',
        unsafe_allow_html=True,
    )

    for view_id, icon, label in NAV_ITEMS:
        active = current == view_id or (view_id == "opportunities" and current == "vacancies")
        if st.sidebar.button(
            f"{icon} {label}",
            key=f"nav_{view_id}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            _go_view(view_id)

    st.sidebar.divider()

    if has_resume and st.sidebar.button("⚙ Career Agent", use_container_width=True):
        go_to_setup()
        st.rerun()


def render_setup_sidebar() -> None:
    render_sidebar_brand()
    st.sidebar.caption("Настройка Career Agent")
    if st.sidebar.button("← К работе", use_container_width=True, type="primary"):
        from ui.workflow import go_to_work

        go_to_work()
        st.rerun()


def source_label(source: str) -> str:
    label, icon = SOURCE_META.get(source, (source, "📋"))
    return f"{icon} {label}"
