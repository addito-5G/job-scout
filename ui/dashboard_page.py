"""Аналитический дашборд по собранным вакансиям."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from ui.data import (
    cached_dashboard_metrics,
    cached_experience_chart,
    cached_match_buckets,
    cached_profile_id,
    cached_source_chart,
    cached_timeline,
    cached_top_companies,
    cached_top_skills,
    cached_work_format_chart,
)
from ui.profile_filter import get_selected_profile_role


def render_dashboard() -> None:
    st.header("📊 Аналитический дашборд")
    profile_id = cached_profile_id()
    profile_role = get_selected_profile_role()
    metrics = cached_dashboard_metrics(profile_id, profile_role)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Всего вакансий", metrics["total"])
    c2.metric("С зарплатой", metrics.get("with_salary", 0))
    c3.metric("Новых за 7 дн.", metrics["new_7d"])
    sal = metrics["median_salary"]
    c4.metric("Медиана ЗП", f"{sal:,} ₽".replace(",", " ") if sal else "—")
    avg = metrics["avg_match_score"]
    c5.metric("Средний match", f"{avg}%" if avg is not None else "—")
    c6.metric("Новых за 30 дн.", metrics["new_30d"])

    row1_l, row1_r = st.columns(2)
    with row1_l:
        st.subheader("Источники")
        sources = cached_source_chart(profile_role)
        if sources:
            fig = px.bar(
                x=[s[0] for s in sources],
                y=[s[1] for s in sources],
                color=[s[0] for s in sources],
            )
            fig.update_layout(showlegend=False, height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    with row1_r:
        st.subheader("Формат работы")
        wf = cached_work_format_chart(profile_role)
        if wf:
            fig = px.pie(names=[x[0] for x in wf], values=[x[1] for x in wf], hole=0.4)
            fig.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    row2_l, row2_r = st.columns(2)
    with row2_l:
        st.subheader("Топ компаний")
        companies = cached_top_companies(8, profile_role)
        if companies:
            fig = px.bar(
                x=[c[1] for c in companies],
                y=[c[0][:40] for c in companies],
                orientation="h",
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=320,
                margin=dict(t=20, b=20),
                xaxis_title="Вакансий",
            )
            st.plotly_chart(fig, use_container_width=True)
    with row2_r:
        st.subheader("Требуемый опыт")
        exp = cached_experience_chart(profile_role)
        if exp:
            fig = px.bar(x=[e[0] for e in exp], y=[e[1] for e in exp])
            fig.update_layout(height=320, margin=dict(t=20, b=20), xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    row3_l, row3_r = st.columns(2)
    with row3_l:
        st.subheader("Топ навыков на рынке")
        skills = cached_top_skills(12, profile_role)
        if skills:
            fig = px.bar(
                x=[s[1] for s in skills],
                y=[s[0] for s in skills],
                orientation="h",
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=320,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
    with row3_r:
        st.subheader("Распределение AI match")
        buckets = cached_match_buckets(profile_id, profile_role)
        if buckets and sum(buckets.values()) > 0:
            fig = px.bar(
                x=list(buckets.keys()),
                y=list(buckets.values()),
                color=list(buckets.keys()),
            )
            fig.update_layout(showlegend=False, height=320, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Запустите матчинг после парсинга — появится распределение совпадений.")

    st.subheader("Динамика появления вакансий")
    timeline = cached_timeline(30, profile_role)
    if timeline:
        fig = px.area(
            x=[t[0] for t in timeline],
            y=[t[1] for t in timeline],
        )
        fig.update_layout(height=280, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
