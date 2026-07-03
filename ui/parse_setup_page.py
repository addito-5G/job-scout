"""Настройка ключей поиска и расписания."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.parse_estimate import estimate_parse_seconds
from services.profile_service import get_latest_profile
from services.schedule_service import save_schedule
from services.search_service import (
    build_search_draft,
    get_active_search_settings,
    save_search_settings,
    search_settings_to_data,
    settings_to_habr_queries_from_data,
    settings_to_queries_from_data,
)
from ui.data import clear_data_cache
from ui.keyword_editor import apply_draft_to_lists, inject_keyword_styles, render_keyword_editor, sync_keyword_lists
from ui.schedule_panel import render_schedule_settings
from ui.workflow import go_to, go_to_work, start_manual_refresh


def _load_draft(session, profile_id: int) -> dict:
    if st.session_state.get("search_draft"):
        return st.session_state.search_draft
    active = get_active_search_settings(session, profile_id)
    if active:
        return search_settings_to_data(active)
    return build_search_draft(session, profile_id)


def _save_profile(session, profile_id: int, preview_data: dict, schedule_data: dict) -> None:
    save_search_settings(session, profile_id, preview_data)
    save_schedule(schedule_data)
    clear_data_cache()
    st.session_state.search_draft = preview_data


def render_keywords_step(*, setup_mode: bool = False) -> None:
    inject_keyword_styles()

    if setup_mode:
        st.markdown("## ⚙️ Настройки поиска")
        st.caption("Профиль поиска действует, пока вы его не измените. Парсинг идёт по расписанию.")
    else:
        st.markdown("## Ключи для поиска")
        st.markdown(
            '<p style="color:#9da7b3;font-size:0.95rem;margin-top:-0.5rem;">'
            "Проверьте списки ниже. После сохранения данные будут собираться автоматически.</p>",
            unsafe_allow_html=True,
        )

    init_db()
    session = get_session()
    try:
        profile = get_latest_profile(session)
        if not profile or not profile.resume_raw:
            st.warning("Сначала загрузите резюме.")
            if st.button("← К резюме"):
                go_to("input")
                st.rerun()
            return

        sync_id = st.session_state.get("processed_resume_id") or f"profile_{profile.id}"
        draft = _load_draft(session, profile.id)
        st.session_state.search_draft = draft
        rev = sync_keyword_lists(draft, sync_id=sync_id)

        if profile.title:
            st.success(f"Целевая должность: **{profile.title}**")

        if st.button("🔄 Переподобрать ключи через AI", type="secondary"):
            with st.spinner("Ollama подбирает ключи..."):
                draft = build_search_draft(session, profile.id)
                st.session_state.search_draft = draft
                apply_draft_to_lists(draft)
            st.toast("Список обновлён", icon="✅")
            st.rerun()

        rev = int(st.session_state.get("kw_rev", rev))

        render_keyword_editor(
            "Должности · HeadHunter",
            "kw_desired_titles",
            kind="title",
            hint="Поисковые запросы на hh.ru",
            rev=rev,
        )

        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            render_keyword_editor(
                "Ключевые слова",
                "kw_keywords_include",
                kind="include",
                hint="Habr Career и Geekjob",
                rev=rev,
            )
        with col_b:
            render_keyword_editor(
                "Исключить",
                "kw_keywords_exclude",
                kind="exclude",
                hint="Не показывать вакансии с этими словами",
                rev=rev,
            )

        desired_titles = list(st.session_state.get("kw_desired_titles", []))
        keywords_include = list(st.session_state.get("kw_keywords_include", []))
        keywords_exclude = list(st.session_state.get("kw_keywords_exclude", []))

        if not desired_titles and not keywords_include:
            st.error("Добавьте хотя бы одну должность или ключевое слово.")
            return

        preview_data = {
            **draft,
            "desired_titles": desired_titles or keywords_include[:3],
            "keywords_include": keywords_include,
            "keywords_exclude": keywords_exclude,
        }
        hh_queries = settings_to_queries_from_data(preview_data)
        habr_queries = settings_to_habr_queries_from_data(preview_data)

        with st.expander("Как будут выглядеть запросы на площадках", expanded=False):
            p1, p2, p3 = st.columns(3)
            with p1:
                st.markdown("**HeadHunter**")
                for q in hh_queries:
                    st.markdown(f"- {q.get('text', q)}")
            with p2:
                st.markdown("**Habr**")
                for q in habr_queries:
                    st.markdown(f"- {q}")
            with p3:
                st.markdown("**Geekjob**")
                for q in habr_queries:
                    st.markdown(f"- {q}")

        schedule_data = render_schedule_settings(expanded=setup_mode or not get_active_search_settings(session, profile.id))

        st.divider()
        btn_save, btn_now = st.columns(2)
        with btn_save:
            save_label = "💾 Сохранить профиль" if setup_mode else "💾 Сохранить и начать работу"
            if st.button(save_label, type="primary", use_container_width=True):
                _save_profile(session, profile.id, preview_data, schedule_data)
                go_to_work()
                st.toast(
                    f"Профиль сохранён. Автообновление в {schedule_data['scan_time']} МСК.",
                    icon="✅",
                )
                st.rerun()
        with btn_now:
            eta_min = max(1, estimate_parse_seconds() // 60)
            if st.button(
                f"🔍 Собрать сейчас (~{eta_min} мин)",
                use_container_width=True,
            ):
                _save_profile(session, profile.id, preview_data, schedule_data)
                start_manual_refresh()
                st.rerun()
    finally:
        session.close()
