"""Боковая навигация основного интерфейса."""

from __future__ import annotations

import streamlit as st

from ui.data import cached_last_scan, cached_schedule_summary, cached_source_counts
from ui.profile_filter import get_selected_profile_role, render_profile_filter_sidebar
from ui.workflow import go_to_setup, reset_to_input, start_manual_refresh

SOURCE_META: dict[str, tuple[str, str]] = {
    "hh": ("HeadHunter", "🟥"),
    "habr": ("Habr Career", "🟦"),
    "geekjob": ("Geekjob", "🟩"),
}


def _go_view(view: str, *, source: str | None = None) -> None:
    st.session_state.view = view
    if source is not None:
        st.session_state.selected_source = source
        st.session_state.vac_page = 1
    if view != "detail":
        st.query_params.clear()


def _render_scan_status() -> None:
    st.sidebar.markdown("**Обновление данных**")
    summary = cached_schedule_summary()
    last = cached_last_scan()

    if last:
        st.sidebar.caption(f"Последний сбор: **{last['finished_at']}**")
        st.sidebar.caption(
            f"Вакансий: {last['total_found']} · новых {last['new_added']}"
        )
    else:
        st.sidebar.warning("Данные ещё не собирались — нажмите «Обновить сейчас».")

    if summary["enabled"]:
        st.sidebar.caption(f"Расписание: ежедневно **{summary['scan_time']}** МСК")
        st.sidebar.caption(f"Следующий запуск: {summary['next_run']}")
    else:
        st.sidebar.caption("Автообновление выключено")

    if st.sidebar.button("🔄 Обновить сейчас", use_container_width=True, type="primary"):
        start_manual_refresh()
        st.rerun()

    st.sidebar.divider()


def render_app_sidebar(*, has_resume: bool) -> None:
    st.sidebar.title("🔎 Job Scout")
    st.sidebar.caption("Режим работы")

    _render_scan_status()

    profile_role = render_profile_filter_sidebar()

    counts = cached_source_counts(profile_role)
    current_view = st.session_state.get("view", "dashboard")

    if st.sidebar.button(
        "📊 Аналитический дашборд",
        use_container_width=True,
        type="primary" if current_view == "dashboard" else "secondary",
    ):
        _go_view("dashboard")
        st.rerun()

    st.sidebar.markdown("**Вакансии по площадкам**")
    for source, (label, icon) in SOURCE_META.items():
        count = counts.get(source, 0)
        active = current_view in ("vacancies", "detail") and st.session_state.get("selected_source") == source
        if st.sidebar.button(
            f"{icon} {label} ({count})",
            key=f"nav_{source}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            _go_view("vacancies", source=source)
            st.rerun()

    st.sidebar.divider()

    if st.sidebar.button("📝 Рекомендации к резюме", use_container_width=True):
        _go_view("resume_advice")
        st.rerun()

    if has_resume and st.sidebar.button("⚙️ Настройки поиска", use_container_width=True):
        go_to_setup()
        st.rerun()

    if has_resume and st.sidebar.button("🔄 Новый поиск", use_container_width=True):
        reset_to_input()
        st.session_state.workflow_stage = "input"
        st.rerun()


def render_setup_sidebar() -> None:
    st.sidebar.title("🔎 Job Scout")
    st.sidebar.caption("Режим настройки")
    if st.sidebar.button("← К работе", use_container_width=True, type="primary"):
        from ui.workflow import go_to_work

        go_to_work()
        st.rerun()


def source_label(source: str) -> str:
    label, icon = SOURCE_META.get(source, (source, "📋"))
    return f"{icon} {label}"
