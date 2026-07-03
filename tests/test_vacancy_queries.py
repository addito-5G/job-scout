"""Тесты SQL builders для списка вакансий."""

from __future__ import annotations

from services.vacancy_queries import build_list_vacancies_base, list_vacancy_filter_conditions
from services.vacancy_service import VacancyFilters


def test_build_list_vacancies_base_without_profile():
    base, match_expr = build_list_vacancies_base(None)
    sql = str(base.compile(compile_kwargs={"literal_binds": True}))
    assert "vacancies" in sql.lower()
    assert "literal(0)" in str(match_expr.compile(compile_kwargs={"literal_binds": True}))


def test_list_vacancy_filter_conditions_respects_profile_role():
    filters = VacancyFilters(profile_role="product_manager", hide_hidden=True)
    _, match_expr = build_list_vacancies_base(1)
    conditions = list_vacancy_filter_conditions(filters, profile_id=1, match_score_expr=match_expr)
    assert len(conditions) >= 2
