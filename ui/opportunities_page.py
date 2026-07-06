"""Best Matches — companies first, then vacancies per company."""

from __future__ import annotations

import math

import streamlit as st

from ui.components import match_score_badge, render_company_card, render_opportunity_card
from ui.data import (
    cached_company_detail,
    cached_company_list,
    cached_opportunity_list,
    cached_profile_id,
)
from ui.design_system import COLORS
from ui.navigation import SOURCE_META

PER_PAGE = 20

SOURCE_TABS = [("all", "Все")] + [(k, v[0]) for k, v in SOURCE_META.items()]


def _render_company_view(
    company_id: int,
    *,
    profile_id: int | None,
    saved_only: bool,
) -> None:
    company = cached_company_detail(company_id, profile_id)
    if not company:
        st.error("Компания не найдена")
        if st.button("← К списку компаний"):
            st.session_state.pop("selected_company_id", None)
            st.session_state.opp_page = 1
            st.rerun()
        return

    if st.button("← К компаниям"):
        st.session_state.pop("selected_company_id", None)
        st.session_state.opp_page = 1
        st.rerun()

    score = company.get("best_match_score")
    st.markdown(
        f'<div class="nm-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">'
        f'<div><div class="nm-eyebrow">Работодатель</div>'
        f'<div style="font-weight:700;font-size:1.35rem">{company["name"]}</div>'
        f'<div style="color:{COLORS["text_muted"]};font-size:0.85rem;margin-top:0.35rem">'
        f'{company["vacancy_count"]} вакансий в вашем профиле'
        f"</div></div>"
        f'<div>{match_score_badge(score)}</div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    brief = (company.get("ai_brief") or "").strip()
    if brief:
        st.markdown(
            f'<div class="nm-section-label">О компании</div>'
            f'<div class="nm-card" style="font-size:0.9rem;line-height:1.55;color:{COLORS["text"]}">'
            f"{brief}</div>",
            unsafe_allow_html=True,
        )
    elif company.get("description"):
        st.markdown(
            f'<div class="nm-section-label">О компании</div>'
            f'<div class="nm-card" style="font-size:0.9rem;line-height:1.55">{company["description"][:500]}</div>',
            unsafe_allow_html=True,
        )

    if company.get("website"):
        st.link_button("Сайт компании", company["website"])

    st.markdown('<div class="nm-section-label">Вакансии</div>', unsafe_allow_html=True)

    source = None if st.session_state.opp_source == "all" else st.session_state.opp_source
    status = "favorite" if saved_only else None
    min_match = st.session_state.get("opp_match", 0)

    items, total = cached_opportunity_list(
        profile_id,
        source,
        min_match,
        st.session_state.get("opp_search", "").strip(),
        st.session_state.opp_page,
        status=status,
        company_id=company_id,
    )

    if not items:
        st.info("Нет вакансий по текущим фильтрам.")
        return

    st.caption(f"{total} вакансий · стр. {st.session_state.opp_page}/{max(1, math.ceil(total / PER_PAGE))}")
    for item in items:
        render_opportunity_card(item, profile_id=profile_id, hide_company=True)

    total_pages = max(1, math.ceil(total / PER_PAGE))
    nav1, _, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.session_state.opp_page > 1 and st.button("← Назад", key="co_back"):
            st.session_state.opp_page -= 1
            st.rerun()
    with nav3:
        if st.session_state.opp_page < total_pages and st.button("Вперёд →", key="co_fwd"):
            st.session_state.opp_page += 1
            st.rerun()


def render_opportunities(*, saved_only: bool = False) -> None:
    st.session_state.setdefault("opp_page", 1)
    st.session_state.setdefault("opp_source", "all")

    profile_id = cached_profile_id()
    company_id = st.session_state.get("selected_company_id")

    title = "⭐ Сохранённые" if saved_only else "🎯 Возможности"
    subtitle = (
        "Вакансии, которые вы отметили для отклика"
        if saved_only
        else "Работодатели с подходящими вакансиями — откройте компанию, чтобы выбрать роль"
    )
    st.markdown(
        f'<div class="nm-eyebrow">{title}</div>'
        f'<div class="nm-title" style="font-size:1.35rem">{title.split(" ", 1)[-1]}</div>'
        f'<p class="nm-subtitle">{subtitle}</p>',
        unsafe_allow_html=True,
    )

    if company_id:
        _render_company_view(int(company_id), profile_id=profile_id, saved_only=saved_only)
        return

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

    items, total = cached_company_list(
        profile_id,
        source,
        min_match,
        search.strip(),
        st.session_state.opp_page,
        status=status,
    )

    total_pages = max(1, math.ceil(total / PER_PAGE))
    st.caption(f"{total} компаний · стр. {st.session_state.opp_page}/{total_pages}")

    if not items:
        st.info(
            "Пока пусто. Запустите сканирование в сайдбаре или снизьте фильтр match."
            if not saved_only
            else "Сохраняйте вакансии кнопкой ⭐ на карточке."
        )
        return

    for item in items:
        render_company_card(item)

    nav1, _, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.session_state.opp_page > 1 and st.button("← Назад", key="opp_back"):
            st.session_state.opp_page -= 1
            st.rerun()
    with nav3:
        if st.session_state.opp_page < total_pages and st.button("Вперёд →", key="opp_fwd"):
            st.session_state.opp_page += 1
            st.rerun()
