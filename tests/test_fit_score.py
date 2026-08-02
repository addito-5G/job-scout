"""Тесты единого fit score."""

from __future__ import annotations

import json

from domain.fit_score import compute_fit, fit_to_match_dict


def _pm_profile():
    return {
        "profile_skills": [
            "Product Manager",
            "SQL",
            "Python",
            "DataLens",
            "CustDev",
            "Roadmap",
            "P&L",
            "Miro",
            "MPSTATS",
            "Agile",
            "Hypothesis Testing",
        ],
        "profile_strengths": [
            "Запуск B2B SaaS с нуля",
            "Управление продуктом на стыке данных и бизнес-метрик",
            "Опыт в e-commerce и retail",
        ],
        "profile_weaknesses": ["Неоконченное высшее образование"],
        "profile_domains": ["B2B SaaS", "e-commerce", "retail"],
        "profile_title": "Product Manager",
        "profile_recommended_roles": ["Product Manager", "Head of Product"],
        "profile_experience_years": 15,
        "profile_ai_summary": "Product Manager с опытом в B2B, e-commerce, unit economics, SQL, Python.",
    }


def test_pm_growth_vacancy_scores_well():
    result = compute_fit(
        **_pm_profile(),
        vacancy_title="Middle+ Product Manager (Growth)",
        vacancy_description=(
            "Ищем PM для growth-направления. SQL, Python, unit economics, "
            "A/B тесты, retention, discovery, roadmap, custdev."
        ),
        vacancy_skills=["Product Manager", "SQL", "Python", "Clickhouse", "Growth"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    assert result.match_score >= 65
    assert result.recommendation in ("apply", "improve_resume")
    assert "SQL" in result.matched_skills or any("sql" in s.lower() for s in result.matched_skills)
    assert result.gaps_to_improve
    assert result.match_score > 0


def test_backend_vacancy_scores_low_for_pm():
    result = compute_fit(
        **_pm_profile(),
        vacancy_title="Senior Backend Developer",
        vacancy_description="Python, Django, PostgreSQL, microservices, Kubernetes",
        vacancy_skills=["Python", "Django", "Kubernetes"],
        vacancy_experience_required="Более 6 лет",
    )
    assert result.match_score < 55
    assert result.recommendation == "skip"


def test_no_zero_when_role_and_skills_overlap():
    result = compute_fit(
        **_pm_profile(),
        vacancy_title="Entrepreneur in Residence (EIR)",
        vacancy_description=(
            "Построить новое направление, AI для B2C, discovery, unit economics, "
            "запуск продукта, stakeholder management."
        ),
        vacancy_skills=["Product Management", "AI", "B2C", "Discovery"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    assert result.match_score >= 50
    assert result.match_score != 0


def test_missing_skills_surface_as_gaps():
    result = compute_fit(
        **_pm_profile(),
        vacancy_title="Product Manager",
        vacancy_description="Нужны UX тесты, дизайн, Figma, SQL, roadmap",
        vacancy_skills=["UX тесты", "Дизайн", "SQL", "Roadmap"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    missing_lower = " ".join(result.missing_skills).lower()
    assert "ux" in missing_lower or "дизайн" in missing_lower or "figma" in missing_lower
    assert any("Усилить" in g for g in result.gaps_to_improve)


def test_must_have_penalty_when_core_skills_missing():
    result = compute_fit(
        profile_skills=["Product Manager", "Roadmap"],
        profile_strengths=["Веду продукт"],
        profile_weaknesses=[],
        profile_domains=["B2B SaaS"],
        profile_title="Product Manager",
        profile_recommended_roles=["Product Manager"],
        profile_experience_years=5,
        vacancy_title="Product Manager",
        vacancy_description=(
            "Обязательно: SQL, Python, unit economics. "
            "Будет плюсом: Figma."
        ),
        vacancy_skills=["SQL", "Python", "Unit economics"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    assert result.match_score < 65
    assert any("обязательн" in r.lower() for r in result.risks) or any(
        "обязательн" in g.lower() for g in result.gaps_to_improve
    )


def test_must_section_in_description_weighted_higher():
    weak = compute_fit(
        profile_skills=["Product Manager", "Roadmap", "Figma"],
        profile_strengths=[],
        profile_weaknesses=[],
        profile_domains=[],
        profile_title="Product Manager",
        profile_recommended_roles=["Product Manager"],
        profile_experience_years=4,
        vacancy_title="Product Manager",
        vacancy_description="Будет плюсом SQL. Нужен общий продуктовый опыт.",
        vacancy_skills=["Roadmap"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    strong = compute_fit(
        profile_skills=["Product Manager", "Roadmap", "SQL", "Python"],
        profile_strengths=["SQL и Python в работе с метриками"],
        profile_weaknesses=[],
        profile_domains=["B2B SaaS"],
        profile_title="Product Manager",
        profile_recommended_roles=["Product Manager"],
        profile_experience_years=4,
        vacancy_title="Product Manager",
        vacancy_description="Обязательно: SQL и Python. Roadmap.",
        vacancy_skills=["SQL", "Python", "Roadmap"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    assert strong.match_score > weak.match_score



def test_fit_to_match_dict_roundtrip():
    result = compute_fit(
        **_pm_profile(),
        vacancy_title="Product Manager",
        vacancy_description="SQL, roadmap, discovery",
        vacancy_skills=["SQL", "Roadmap"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    data = fit_to_match_dict(result)
    assert 0 <= data["match_score"] <= 100
    assert isinstance(data["matched_skills"], list)
    assert data["recommendation"] in ("apply", "improve_resume", "skip")


def test_score_never_applies_with_zero_overlap():
    result = compute_fit(
        profile_skills=["Java", "Spring"],
        profile_strengths=[],
        profile_weaknesses=[],
        profile_domains=["fintech"],
        profile_title="Java Developer",
        profile_recommended_roles=["Java Developer"],
        profile_experience_years=5,
        vacancy_title="Product Manager",
        vacancy_description="product discovery roadmap custdev",
        vacancy_skills=["CustDev", "Roadmap", "Discovery"],
        vacancy_experience_required="От 3 до 6 лет",
    )
    assert result.match_score < 72
