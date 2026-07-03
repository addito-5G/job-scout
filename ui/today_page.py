"""Today — daily career briefing (home)."""

from __future__ import annotations

import streamlit as st

from db import get_session, init_db
from services.profile_service import get_latest_profile
from services.today_service import build_today_briefing
from ui.components import match_score_class
from ui.data import cached_profile_id
from ui.design_system import COLORS
from ui.profile_filter import get_selected_profile_role


def _go(view: str, **kwargs) -> None:
    st.session_state.view = view
    for k, v in kwargs.items():
        st.session_state[k] = v
    if view != "detail":
        st.query_params.clear()
    st.rerun()


def render_today() -> None:
    profile_id = cached_profile_id()
    profile_role = get_selected_profile_role()

    init_db()
    session = get_session()
    try:
        profile = get_latest_profile(session)
        briefing = build_today_briefing(
            session,
            profile_id,
            profile_role=profile_role,
            full_name=profile.full_name if profile else None,
        )
    finally:
        session.close()

    name = briefing["greeting_name"]
    st.markdown(
        f'<div class="nm-card-hero">'
        f'<div class="nm-eyebrow">Сегодня</div>'
        f'<div class="nm-title">Доброе утро, {name} 👋</div>'
        f'<p class="nm-subtitle">Что сделать сегодня, чтобы приблизиться к офферу</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    top = briefing.get("top_opportunity")
    if top:
        mc = match_score_class(top.get("match_score"))
        cta_col, info_col = st.columns([1, 2])
        with cta_col:
            st.markdown(
                f'<div class="nm-card" style="text-align:center">'
                f'<div class="nm-eyebrow">Главное действие</div>'
                f'<div class="nm-match-lg {mc}">{top.get("match_score") or "—"}%</div>'
                f'<div style="color:{COLORS["text_muted"]};font-size:0.8rem;margin-top:0.25rem">match</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button("Откликнуться →", type="primary", use_container_width=True, key="today_cta"):
                st.session_state.view = "detail"
                st.session_state.selected_vacancy_id = top["id"]
                st.query_params["vacancy_id"] = str(top["id"])
                st.rerun()
        with info_col:
            st.markdown(
                f'<div class="nm-card">'
                f'<div style="font-weight:600;font-size:1.05rem;margin-bottom:0.35rem">{top["title"]}</div>'
                f'<div style="color:{COLORS["text_muted"]};font-size:0.85rem">{top.get("company") or "Компания не указана"}</div>'
                f'<div style="margin-top:0.75rem;font-size:0.85rem;color:{COLORS["text"]}">'
                f"AI рекомендует откликнуться — высокое совпадение с вашим профилем."
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="nm-section-label">Ваш день</div>', unsafe_allow_html=True)
    insights_html = '<div class="nm-card">'
    for item in briefing["insights"]:
        insights_html += f'<div class="nm-insight"><span class="nm-dot"></span><span>{item["text"]}</span></div>'
    insights_html += "</div>"
    st.markdown(insights_html, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Возможностей", briefing["total_opportunities"])
    m2.metric("Новых", briefing["new_opportunities"])
    m3.metric("Match ≥90%", briefing["excellent_matches"])
    m4.metric("В работе", briefing["pipeline_count"])

    st.markdown('<div class="nm-section-label">Быстрые действия</div>', unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("🎯 Возможности", use_container_width=True):
            _go("opportunities")
    with a2:
        if st.button("📄 Резюме", use_container_width=True):
            _go("resume")
    with a3:
        if st.button("✉ Отклики", use_container_width=True):
            _go("applications")
    with a4:
        if st.button("📈 Рынок", use_container_width=True):
            _go("insights")
