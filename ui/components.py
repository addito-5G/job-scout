"""Переиспользуемые UI-компоненты."""

from __future__ import annotations

import streamlit as st

from ui.design_system import COLORS
from ui.navigation import source_label


def match_score_class(score: int | None) -> str:
    if score is None:
        return "nm-match-low"
    if score >= 90:
        return "nm-match-excellent"
    if score >= 75:
        return "nm-match-good"
    if score >= 50:
        return "nm-match-ok"
    return "nm-match-low"


def match_score_badge(score: int | None) -> str:
    if score is None:
        return '<span class="nm-badge">—</span>'
    cls = match_score_class(score)
    return f'<span class="nm-match-lg {cls}">{score}%</span>'


def skill_badges(skills: list[str], *, kind: str = "match") -> None:
    if not skills:
        st.caption("—")
        return
    bg = "#1a2e1f" if kind == "match" else "#2e1a1a"
    fg = "#3ecf8e" if kind == "match" else "#e5484d"
    html = " ".join(
        f'<span style="background:{bg};color:{fg};padding:3px 9px;'
        f'border-radius:6px;margin:2px;display:inline-block;font-size:0.78rem;">{s}</span>'
        for s in skills[:8]
    )
    st.markdown(html, unsafe_allow_html=True)


def format_salary(item) -> str:
    if getattr(item, "salary", None):
        return item.salary
    if getattr(item, "salary_text", None):
        return item.salary_text
    smin = getattr(item, "salary_min", None) or getattr(item, "salary_from", None)
    smax = getattr(item, "salary_max", None) or getattr(item, "salary_to", None)
    if smin and smax:
        return f"{smin:,} – {smax:,} ₽".replace(",", " ")
    if smin:
        return f"от {smin:,} ₽".replace(",", " ")
    if smax:
        return f"до {smax:,} ₽".replace(",", " ")
    return "не указана"


def work_format_label(fmt: str | None) -> str:
    labels = {
        "remote": "Удалённо",
        "office": "Офис",
        "hybrid": "Гибрид",
    }
    return labels.get(fmt or "", fmt or "—")


def render_opportunity_card(item: dict, *, profile_id: int | None) -> None:
    """Linear-style dense opportunity card."""
    vid = item["id"]
    score = item.get("match_score")
    mc = match_score_class(score)
    salary = format_salary(type("O", (), item)())
    wf = work_format_label(item.get("work_format"))
    source = source_label(item.get("source", "")) if item.get("source") else ""
    rec = item.get("recommendation") or ""
    rec_label = {"apply": "Откликаться", "skip": "Пропустить", "improve_resume": "Усилить резюме"}.get(
        rec, rec
    )

    st.markdown(
        f'<div class="nm-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">'
        f'<div style="flex:1;min-width:0">'
        f'<div style="font-weight:600;font-size:1rem;margin-bottom:0.25rem">{item["title"]}</div>'
        f'<div style="color:{COLORS["text_muted"]};font-size:0.82rem">'
        f'{item.get("company") or "—"} · {wf} · {salary}'
        f"</div>"
        f'<div style="margin-top:0.5rem">'
        f'<span class="nm-badge">{source}</span> '
        f'<span class="nm-badge">{rec_label}</span>'
        f"</div></div>"
        f'<div style="text-align:right;flex-shrink:0">'
        f'<div class="nm-match-lg {mc}">{score or "—"}%</div>'
        f'<div style="font-size:0.7rem;color:{COLORS["text_subtle"]}">match</div>'
        f"</div></div></div>",
        unsafe_allow_html=True,
    )

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Открыть", key=f"open_{vid}", use_container_width=True):
            st.session_state.view = "detail"
            st.session_state.selected_vacancy_id = vid
            st.query_params["vacancy_id"] = str(vid)
            st.rerun()
    with b2:
        if st.button("⭐", key=f"fav_{vid}", use_container_width=True):
            _set_status(vid, "favorite")
    with b3:
        if st.button("✅ Отклик", key=f"app_{vid}", use_container_width=True):
            _set_status(vid, "applied")
    with b4:
        if st.button("Скрыть", key=f"hide_{vid}", use_container_width=True):
            _set_status(vid, "hidden")


def _set_status(vacancy_id: int, status: str) -> None:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "src"))
    from db import get_session, init_db
    from services.vacancy_service import update_vacancy_status
    from ui.data import clear_data_cache

    init_db()
    session = get_session()
    try:
        update_vacancy_status(session, vacancy_id, status)
    finally:
        session.close()
    clear_data_cache()
    st.toast("Сохранено", icon="✅")
    st.rerun()
