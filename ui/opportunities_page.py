"""Best Matches — unified opportunity list."""

from __future__ import annotations

import math

import streamlit as st

from ui.components import render_opportunity_card
from ui.data import cached_opportunity_list, cached_profile_id
from ui.design_system import COLORS
from ui.navigation import SOURCE_META
from ui.profile_filter import get_selected_profile_role

PER_PAGE = 20

SOURCE_TABS = [("all", "Все")] + [(k, v[0]) for k, v in SOURCE_META.items()]


def render_opportunities(*, saved_only: bool = False) -> None:
    st.session_state.setdefault("opp_page", 1)
    st.session_state.setdefault("opp_source", "all")

    profile_id = cached_profile_id()
    profile_role = get_selected_profile_role()

    title = "⭐ Сохранённые" if saved_only else "🎯 Возможности"
    subtitle = (
        "Вакансии, которые вы отметили для отклика"
        if saved_only
        else "Приоритизированные возможности — отвечайте: стоит ли откликаться?"
    )
    st.markdown(
        f'<div class="nm-eyebrow">{title}</div>'
        f'<div class="nm-title" style="font-size:1.35rem">{title.split(" ", 1)[-1]}</div>'
        f'<p class="nm-subtitle">{subtitle}</p>',
        unsafe_allow_html=True,
    )

    if not saved_only:
        tab_cols = st.columns(len(SOURCE_TABS))
        for col, (key, label) in zip(tab_cols, SOURCE_TABS):
            with col:
                active = st.session_state.opp_source == key
                if st.button(
                    label,
                    key=f"tab_{key}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    st.session_state.opp_source = key
                    st.session_state.opp_page = 1
                    st.rerun()

    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input("Поиск", placeholder="Компания или должность…", key="opp_search")
    with c2:
        min_match = st.slider("Min match %", 0, 100, 0, step=5, key="opp_match")

    source = None if st.session_state.opp_source == "all" else st.session_state.opp_source
    status = "favorite" if saved_only else None

    items, total = cached_opportunity_list(
        profile_id,
        source,
        min_match,
        search.strip(),
        st.session_state.opp_page,
        profile_role,
        status=status,
    )

    total_pages = max(1, math.ceil(total / PER_PAGE))
    st.caption(f"{total} возможностей · стр. {st.session_state.opp_page}/{total_pages}")

    if not items:
        st.info(
            "Пока пусто. Запустите сканирование в сайдбаре или снизьте фильтр match."
            if not saved_only
            else "Сохраняйте вакансии кнопкой ⭐ на карточке."
        )
        return

    for item in items:
        render_opportunity_card(item, profile_id=profile_id)

    nav1, _, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.session_state.opp_page > 1 and st.button("← Назад", key="opp_back"):
            st.session_state.opp_page -= 1
            st.rerun()
    with nav3:
        if st.session_state.opp_page < total_pages and st.button("Вперёд →", key="opp_fwd"):
            st.session_state.opp_page += 1
            st.rerun()
