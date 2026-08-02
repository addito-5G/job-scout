"""Прогресс парсинга вакансий."""

from __future__ import annotations

import time

import streamlit as st


from services.refresh_service import refresh_vacancies
from services.scan_progress import label_for
from ui.data import clear_data_cache
from ui.workflow import go_to


def _format_eta(seconds: int) -> str:
    mm, ss = divmod(max(0, seconds), 60)
    return f"{mm}:{ss:02d}"


def run_parse_with_progress() -> None:
    eta_total = int(st.session_state.get("parse_eta_seconds", 600))

    st.sidebar.markdown("### ⏳ Парсинг вакансий")
    st.sidebar.caption("Не закрывайте вкладку.")

    sidebar_progress = st.sidebar.progress(0.0, text="Подготовка...")
    sidebar_status = st.sidebar.empty()
    sidebar_timer = st.sidebar.empty()
    sidebar_source = st.sidebar.empty()

    st.markdown("## Собираем вакансии")
    main_progress = st.progress(0.0, text="Подготовка...")
    main_source = st.empty()
    main_status = st.empty()
    main_timer = st.empty()

    started = float(st.session_state.get("parse_started_at", time.time()))

    def on_progress(value: float, message: str, source: str | None = None) -> None:
        value = min(max(value, 0.0), 1.0)
        elapsed = int(time.time() - started)
        remaining = int(eta_total * (1.0 - value))
        timer_text = f"⏱ Прошло **{_format_eta(elapsed)}** · осталось ≈ **{_format_eta(remaining)}**"

        sidebar_progress.progress(value, text=message)
        sidebar_status.caption(message)
        sidebar_timer.markdown(timer_text)

        main_progress.progress(value, text=message)
        main_status.caption(message)
        main_timer.markdown(timer_text)

        if source:
            st.session_state.parse_current_source = source
            label = label_for(source)
            source_line = f"### 🔄 Сейчас парсим: **{label}**"
            sidebar_source.markdown(source_line)
            main_source.markdown(source_line)

    try:
        result = refresh_vacancies(match_limit=50, progress=on_progress)
        clear_data_cache()
        done_text = "Готово"
        sidebar_progress.progress(1.0, text=done_text)
        main_progress.progress(1.0, text=done_text)
        sidebar_timer.markdown("⏱ Прошло **готово**")
        st.session_state.app_unlocked = True
        go_to("app")
        if st.session_state.get("view") == "setup":
            st.session_state.view = "today"

        errors = list(result.errors or [])
        if result.scraped == 0 and errors:
            st.error(
                "Скан завершился без вакансий. Причины:\n\n- "
                + "\n- ".join(e[:300] for e in errors[:5])
            )
            st.sidebar.error("0 вакансий — см. ошибки на странице")
        elif result.scraped == 0:
            st.warning(
                "Скан завершился: **0** вакансий. Проверьте ключи поиска и период."
            )
            st.sidebar.warning("0 вакансий")
        else:
            st.success(
                f"Собрано **{result.scraped}** вакансий (новых **{result.new_count}**). "
                f"AI-матчинг: **{result.matched}** вакансий. "
                f"Откройте «Сегодня» или «Возможности»."
            )
            st.sidebar.success(
                f"Готово: {result.scraped} вакансий, новых {result.new_count}, "
                f"матчинг {result.matched}"
            )
        if errors and result.scraped > 0:
            st.warning(
                "Частичные ошибки:\n\n- " + "\n- ".join(e[:300] for e in errors[:5])
            )
        st.rerun()
    except Exception as exc:
        st.sidebar.error(f"Ошибка: {exc}")
        st.error(f"Парсинг прерван: {exc}")
        go_to("app")
        st.session_state.view = "dashboard"
    finally:
        st.session_state.refresh_running = False
        st.session_state.pop("parse_started_at", None)
        st.session_state.pop("parse_current_source", None)
