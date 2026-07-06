"""Market Insights — actionable market intelligence."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from ui.data import (
    cached_dashboard_metrics,
    cached_match_buckets,
    cached_profile_id,
    cached_top_skills,
    cached_work_format_chart,
)
from ui.design_system import COLORS
from ui.profile_filter import get_active_resume_profile_label


def _insight_cards(metrics: dict, buckets: dict, skills: list) -> None:
    insights: list[str] = []
    if metrics.get("new_7d"):
        insights.append(f"За 7 дней появилось {metrics['new_7d']} новых вакансий — рынок активен")
    if metrics.get("avg_match_score"):
        insights.append(
            f"Ваш средний match — {metrics['avg_match_score']}%. "
            "Цель: 85%+ через усиление резюме"
        )
    if metrics.get("median_salary"):
        sal = f"{metrics['median_salary']:,}".replace(",", " ")
        insights.append(f"Медианная зарплата в выборке: {sal} ₽")
    if skills:
        insights.append(f"Самый востребованный навык: **{skills[0][0]}** ({skills[0][1]} вакансий)")
    high = buckets.get("90-100", 0) + buckets.get("80-89", 0)
    if high:
        insights.append(f"{high} вакансий с match ≥ 80% — приоритет для откликов")

    html = '<div class="nm-card">'
    for text in insights[:5]:
        html += f'<div class="nm-insight"><span class="nm-dot"></span><span>{text}</span></div>'
    if not insights:
        html += '<div class="nm-insight"><span class="nm-dot"></span><span>Соберите данные — появятся инсайты</span></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_market_insights() -> None:
    profile_id = cached_profile_id()
    metrics = cached_dashboard_metrics(profile_id)

    st.markdown(
        '<div class="nm-eyebrow">Рынок</div>'
        '<div class="nm-title" style="font-size:1.35rem">Market Insights</div>'
        '<p class="nm-subtitle">Не графики ради графиков — что менять в стратегии поиска</p>',
        unsafe_allow_html=True,
    )

    _insight_cards(
        metrics,
        cached_match_buckets(profile_id),
        cached_top_skills(8, profile_id),
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Вакансий", metrics["total"])
    c2.metric("Новых / 7д", metrics["new_7d"])
    c3.metric("Средний match", f"{metrics['avg_match_score']}%" if metrics.get("avg_match_score") else "—")
    sal = metrics.get("median_salary")
    c4.metric("Медиана ЗП", f"{sal:,} ₽".replace(",", " ") if sal else "—")

    row1_l, row1_r = st.columns(2)
    with row1_l:
        st.markdown('<div class="nm-section-label">Формат работы</div>', unsafe_allow_html=True)
        wf = cached_work_format_chart(profile_id)
        if wf:
            fig = px.pie(
                names=[x[0] for x in wf],
                values=[x[1] for x in wf],
                hole=0.55,
                color_discrete_sequence=[COLORS["accent"], COLORS["success"], COLORS["warning"]],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=COLORS["text_muted"],
                height=280,
                margin=dict(t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
    with row1_r:
        st.markdown('<div class="nm-section-label">Распределение match</div>', unsafe_allow_html=True)
        buckets = cached_match_buckets(profile_id)
        if buckets and sum(buckets.values()) > 0:
            fig = px.bar(
                x=list(buckets.keys()),
                y=list(buckets.values()),
                color_discrete_sequence=[COLORS["accent"]],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=COLORS["text_muted"],
                height=280,
                margin=dict(t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
