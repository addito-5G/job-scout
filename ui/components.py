"""Переиспользуемые UI-компоненты."""

from __future__ import annotations

import streamlit as st


def match_score_badge(score: int | None) -> str:
    if score is None:
        return "⚪ —"
    if score > 70:
        color = "#16a34a"
        icon = "🟢"
    elif score >= 40:
        color = "#ca8a04"
        icon = "🟡"
    else:
        color = "#dc2626"
        icon = "🔴"
    return (
        f'<span style="background:{color}22;color:{color};padding:2px 10px;'
        f'border-radius:12px;font-weight:600;">{icon} {score}%</span>'
    )


def skill_badges(skills: list[str], *, kind: str = "match") -> None:
    if not skills:
        st.caption("—")
        return
    bg = "#dcfce7" if kind == "match" else "#fee2e2"
    fg = "#166534" if kind == "match" else "#991b1b"
    html = " ".join(
        f'<span style="background:{bg};color:{fg};padding:4px 10px;'
        f'border-radius:8px;margin:2px;display:inline-block;font-size:0.85rem;">{s}</span>'
        for s in skills
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
        "remote": "🏠 Удалённо",
        "office": "🏢 Офис",
        "hybrid": "🔀 Гибрид",
    }
    return labels.get(fmt or "", fmt or "—")
