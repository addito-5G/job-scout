"""Блок настроек расписания автообновления."""

from __future__ import annotations


import streamlit as st


from services.schedule_service import load_schedule, next_scan_label, save_schedule


def render_schedule_settings(*, expanded: bool = True) -> dict:
    schedule = load_schedule()
    with st.expander("🕘 Расписание автообновления", expanded=expanded):
        st.caption(
            "Фоновый сбор вакансий по расписанию. Утром открываете приложение — данные уже готовы."
        )
        enabled = st.toggle("Включить ежедневное обновление", value=bool(schedule.get("enabled", True)))
        col1, col2 = st.columns(2)
        with col1:
            scan_time = st.text_input(
                "Время (МСК)",
                value=str(schedule.get("scan_time", "09:00")),
                help="Формат ЧЧ:ММ, часовой пояс Europe/Moscow",
            )
        with col2:
            match_limit = st.number_input(
                "Лимит AI-матчинга",
                min_value=10,
                max_value=200,
                value=int(schedule.get("match_limit", 50)),
                step=10,
            )
        if enabled:
            st.info(f"Следующий автозапуск: **{next_scan_label()}** (МСК)")
        else:
            st.warning("Автообновление выключено — только ручной запуск «Обновить сейчас».")
        st.caption(
            "Для фонового запуска установите расписание: "
            "`bash scripts/install_schedule.sh`"
        )
    return {
        "enabled": enabled,
        "scan_time": scan_time.strip(),
        "timezone": "Europe/Moscow",
        "match_limit": int(match_limit),
    }
