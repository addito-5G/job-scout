"""Единый детерминированный скоринг соответствия профиля и вакансии."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

ROLE_STOPWORDS = frozenset(
    {
        "middle",
        "middle+",
        "senior",
        "junior",
        "lead",
        "head",
        "staff",
        "principal",
        "in",
        "the",
        "of",
        "for",
        "and",
        "or",
        "at",
        "eir",
        "residence",
        "entrepreneur",
        "и",
        "в",
        "на",
        "для",
        "со",
        "remote",
        "удаленно",
        "удалённо",
        "гибрид",
        "hybrid",
        "uzum",
    }
)

SKILL_GROUPS: dict[str, frozenset[str]] = {
    "product manager": frozenset(
        {
            "product manager",
            "product owner",
            "product lead",
            "pm",
            "продакт",
            "продакт-менеджер",
            "product management",
            "product",
            "продуктовый менеджер",
            "продуктовый",
        }
    ),
    "sql": frozenset({"sql", "postgresql", "postgres", "mysql", "clickhouse", "click house"}),
    "python": frozenset({"python", "py"}),
    "agile": frozenset({"agile", "scrum", "kanban"}),
    "unit economics": frozenset(
        {"unit economics", "unit economic", "ltv", "cac", "arppu", "unit-экономика", "юнит-экономика"}
    ),
    "discovery": frozenset({"discovery", "custdev", "customer development", "jtbd", "jobs to be done"}),
    "roadmap": frozenset({"roadmap", "дорожная карта", "бэклог", "backlog"}),
    "analytics": frozenset(
        {"analytics", "аналитика", "data-driven", "метрики", "metrics", "a/b", "ab test", "ab-тест"}
    ),
    "growth": frozenset({"growth", "growth hacking", "ретеншн", "retention", "acquisition"}),
    "ux": frozenset({"ux", "ux test", "ux-тест", "ux тесты", "usability", "юзабилити"}),
    "design": frozenset({"design", "дизайн", "ui", "figma"}),
    "ai": frozenset({"ai", "ml", "machine learning", "искусственный интеллект", "нейросет"}),
    "stakeholder": frozenset({"stakeholder", "стейкхолдер", "stakeholder management"}),
    "gtm": frozenset({"gtm", "go-to-market", "go to market", "вывод на рынок"}),
    "p&l": frozenset({"p&l", "pnl", "p/l", "profit and loss"}),
}

DESCRIPTION_TERMS_RE = re.compile(
    r"\b("
    r"sql|python|agile|scrum|jira|miro|custdev|discovery|roadmap|"
    r"a/b|ab[- ]?test|ux|ui|figma|fintech|saas|b2b|b2c|growth|"
    r"ai|ml|unit economics|stakeholder|gtm|mvp|analytics|"
    r"clickhouse|datalens|retention|ltv|cac|hypothesis|гипотез|воронк|метрик|продукт"
    r")\b",
    re.IGNORECASE,
)

EXPERIENCE_MIN_YEARS: dict[str, int] = {
    "без опыта": 0,
    "менее 1 года": 0,
    "от 1 до 3 лет": 1,
    "от 3 до 6 лет": 3,
    "более 6 лет": 6,
}


@dataclass
class FitResult:
    match_score: int
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    gaps_to_improve: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendation: str = "skip"
    match_summary: str = ""


def _loads(raw: str | None, default: list | None = None) -> list:
    if default is None:
        default = []
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return default


def _normalize(text: str) -> str:
    t = (text or "").lower().strip().replace("ё", "е")
    t = re.sub(r"[^\w\s+#&/-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _skill_canonical(skill: str) -> str | None:
    n = _normalize(skill)
    if len(n) < 2:
        return None
    for canonical, variants in SKILL_GROUPS.items():
        if n in variants:
            return canonical
        for v in variants:
            if len(v) >= 3 and (v in n or n in v):
                return canonical
    return n


def _skills_equivalent(a: str, b: str) -> bool:
    ca, cb = _skill_canonical(a), _skill_canonical(b)
    if not ca or not cb:
        return False
    return ca == cb


def _tokenize_title(text: str) -> set[str]:
    tokens = set()
    for part in re.split(r"[/(),+|·\-–—]", text or ""):
        for word in _normalize(part).split():
            if len(word) >= 3 and word not in ROLE_STOPWORDS:
                tokens.add(word)
    return tokens


def _extract_requirements(
    *,
    title: str,
    description: str,
    vacancy_skills: list[str],
) -> list[str]:
    seen: set[str] = set()
    requirements: list[str] = []

    def add(req: str) -> None:
        clean = req.strip()
        if not clean:
            return
        key = _skill_canonical(clean) or _normalize(clean)
        if key in seen:
            return
        seen.add(key)
        requirements.append(clean)

    for skill in vacancy_skills:
        add(skill)

    for match in DESCRIPTION_TERMS_RE.finditer(description or ""):
        add(match.group(0))

    title_tokens = _tokenize_title(title)
    role_hints = {"manager", "analyst", "owner", "lead", "engineer", "developer", "growth", "product", "продукт"}
    for token in title_tokens:
        if token in role_hints or token in SKILL_GROUPS:
            add(token)

    if not requirements and title:
        for token in sorted(title_tokens)[:6]:
            add(token)

    return requirements[:20]


def _profile_capabilities(
    *,
    skills: list[str],
    strengths: list[str],
    domains: list[str],
    title: str | None,
    recommended_roles: list[str],
    ai_summary: str | None,
    experience_summary: str | None,
) -> list[str]:
    caps: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        clean = item.strip()
        if not clean:
            return
        key = _skill_canonical(clean) or _normalize(clean)
        if key in seen:
            return
        seen.add(key)
        caps.append(clean)

    for item in [*skills, *domains, *recommended_roles]:
        add(str(item))
    if title:
        add(title)
    for strength in strengths:
        add(strength)
        for match in DESCRIPTION_TERMS_RE.finditer(strength):
            add(match.group(0))

    blob = " ".join(filter(None, [ai_summary, experience_summary]))
    for match in DESCRIPTION_TERMS_RE.finditer(blob):
        add(match.group(0))

    return caps


def _match_requirements(
    requirements: list[str],
    capabilities: list[str],
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []

    for req in requirements:
        if any(_skills_equivalent(req, cap) for cap in capabilities):
            matched.append(req)
        else:
            missing.append(req)

    return matched, missing


def _role_fit_score(
    vacancy_title: str,
    profile_title: str | None,
    recommended_roles: list[str],
) -> float:
    vac_tokens = _tokenize_title(vacancy_title)
    profile_tokens: set[str] = set()
    if profile_title:
        profile_tokens |= _tokenize_title(profile_title)
    for role in recommended_roles:
        profile_tokens |= _tokenize_title(str(role))

    if not vac_tokens:
        return 0.5

    overlap = vac_tokens & profile_tokens
    ratio = len(overlap) / len(vac_tokens)

    vac_canonical = {_skill_canonical(t) or t for t in vac_tokens}
    prof_canonical = {_skill_canonical(t) or t for t in profile_tokens}
    if "product manager" in vac_canonical and "product manager" in prof_canonical:
        ratio = max(ratio, 0.85)
    if "growth" in vac_canonical and ("growth" in prof_canonical or "product manager" in prof_canonical):
        ratio = max(ratio, 0.7)

    return min(1.0, ratio)


def _experience_fit_score(profile_years: int | None, required_label: str | None) -> float:
    if not required_label:
        return 0.75 if (profile_years or 0) >= 3 else 0.5
    label = _normalize(required_label)
    required = 3
    for key, years in EXPERIENCE_MIN_YEARS.items():
        if key in label:
            required = years
            break
    else:
        m = re.search(r"(\d+)\s*\+", label)
        if m:
            required = int(m.group(1))

    years = profile_years or 0
    if years >= required:
        return 1.0
    if years >= max(0, required - 2):
        return 0.65
    if years >= 1 and required <= 3:
        return 0.5
    return 0.25


def _domain_fit_score(domains: list[str], description: str, vacancy_title: str) -> float:
    if not domains:
        return 0.5
    blob = _normalize(f"{description} {vacancy_title}")
    hits = sum(1 for d in domains if _normalize(str(d)) in blob or _normalize(str(d))[:4] in blob)
    return min(1.0, hits / max(1, min(len(domains), 3)))


def _recommendation_for_score(score: int) -> str:
    if score >= 72:
        return "apply"
    if score >= 50:
        return "improve_resume"
    return "skip"


def _build_gaps(missing: list[str]) -> list[str]:
    tips: list[str] = []
    for item in missing[:6]:
        label = item.strip()
        if not label:
            continue
        tips.append(f"Усилить в резюме и опыте: {label}")
    return tips


def _build_strengths(
    matched: list[str],
    strengths: list[str],
    vacancy_title: str,
) -> list[str]:
    result: list[str] = []
    title_blob = _normalize(vacancy_title)

    for m in matched[:5]:
        result.append(f"Совпадает требование: {m}")

    for s in strengths:
        s_norm = _normalize(s)
        if any(tok in s_norm for tok in _tokenize_title(vacancy_title)):
            result.append(s)
        elif len(result) < 6 and len(s) <= 120:
            result.append(s)

    if not result and matched:
        result.append(f"Покрыто ключевых требований: {len(matched)}")

    return result[:6]


def _build_risks(
    missing: list[str],
    weaknesses: list[str],
    profile_years: int | None,
    required_label: str | None,
) -> list[str]:
    risks: list[str] = []
    for item in missing[:3]:
        risks.append(f"Нет явного подтверждения: {item}")

    for w in weaknesses[:2]:
        if w and w not in risks:
            risks.append(w)

    if required_label and profile_years is not None:
        req_years = _experience_fit_score(profile_years, required_label)
        if req_years < 0.65:
            risks.append(f"Опыт {profile_years} лет может выглядеть слабее ожидания «{required_label}»")

    return risks[:5]


def _build_summary(
    score: int,
    vacancy_title: str,
    matched: list[str],
    missing: list[str],
    total_reqs: int,
) -> str:
    if total_reqs == 0:
        return f"Соответствие с «{vacancy_title}» оценено по роли и профилю: {score}%."

    covered = len(matched)
    if score >= 72:
        tone = "Сильное совпадение"
    elif score >= 50:
        tone = "Умеренное совпадение"
    else:
        tone = "Слабое совпадение"

    gap = ""
    if missing:
        gap = f" Стоит усилить: {', '.join(missing[:3])}."
    return (
        f"{tone} с «{vacancy_title}»: закрыто {covered} из {total_reqs} ключевых требований "
        f"({score}%).{gap}"
    )


def compute_fit(
    *,
    profile_skills: list[str],
    profile_strengths: list[str],
    profile_weaknesses: list[str],
    profile_domains: list[str],
    profile_title: str | None,
    profile_recommended_roles: list[str],
    profile_experience_years: int | None,
    profile_ai_summary: str | None = None,
    profile_experience_summary: str | None = None,
    vacancy_title: str,
    vacancy_description: str,
    vacancy_skills: list[str],
    vacancy_experience_required: str | None = None,
) -> FitResult:
    requirements = _extract_requirements(
        title=vacancy_title,
        description=vacancy_description,
        vacancy_skills=vacancy_skills,
    )
    capabilities = _profile_capabilities(
        skills=profile_skills,
        strengths=profile_strengths,
        domains=profile_domains,
        title=profile_title,
        recommended_roles=profile_recommended_roles,
        ai_summary=profile_ai_summary,
        experience_summary=profile_experience_summary,
    )

    matched, missing = _match_requirements(requirements, capabilities)
    total_reqs = len(requirements)

    if total_reqs:
        skill_ratio = len(matched) / total_reqs
    else:
        skill_ratio = _role_fit_score(vacancy_title, profile_title, profile_recommended_roles)

    role_score = _role_fit_score(vacancy_title, profile_title, profile_recommended_roles)
    exp_score = _experience_fit_score(profile_experience_years, vacancy_experience_required)
    domain_score = _domain_fit_score(profile_domains, vacancy_description, vacancy_title)

    raw = (
        skill_ratio * 50.0
        + role_score * 25.0
        + exp_score * 15.0
        + domain_score * 10.0
    )

    if total_reqs >= 5 and len(matched) >= 3:
        raw += min(8.0, len(matched) * 1.5)
    if len(missing) >= 4 and skill_ratio < 0.5:
        raw -= 8.0

    score = int(max(0, min(100, round(raw))))

    if role_score >= 0.7 and score < 45:
        score = 45
    if skill_ratio >= 0.6 and score < 55:
        score = max(score, 55)
    if skill_ratio >= 0.75 and role_score >= 0.5 and score < 68:
        score = max(score, 68)

    recommendation = _recommendation_for_score(score)
    gaps = _build_gaps(missing)
    strengths = _build_strengths(matched, profile_strengths, vacancy_title)
    risks = _build_risks(missing, profile_weaknesses, profile_experience_years, vacancy_experience_required)
    summary = _build_summary(score, vacancy_title, matched, missing, total_reqs)

    return FitResult(
        match_score=score,
        matched_skills=matched,
        missing_skills=missing,
        gaps_to_improve=gaps,
        strengths=strengths,
        risks=risks,
        recommendation=recommendation,
        match_summary=summary,
    )


def fit_from_profile_model(profile, vacancy, vacancy_skills: list[str]) -> FitResult:
    """Удобная обёртка для ORM-моделей CandidateProfile и Vacancy."""
    return compute_fit(
        profile_skills=_loads(profile.skills_json),
        profile_strengths=_loads(profile.strengths_json),
        profile_weaknesses=_loads(profile.weaknesses_json),
        profile_domains=_loads(profile.domains_json),
        profile_title=profile.title,
        profile_recommended_roles=_loads(profile.recommended_roles_json),
        profile_experience_years=profile.experience_years,
        profile_ai_summary=profile.ai_summary,
        profile_experience_summary=profile.experience_summary,
        vacancy_title=vacancy.title,
        vacancy_description=vacancy.description_full or vacancy.description_short or "",
        vacancy_skills=vacancy_skills,
        vacancy_experience_required=vacancy.experience_required,
    )


def fit_to_match_dict(result: FitResult) -> dict:
    return {
        "match_score": result.match_score,
        "match_summary": result.match_summary,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
        "gaps_to_improve": result.gaps_to_improve,
        "strengths": result.strengths,
        "risks": result.risks,
        "recommendation": result.recommendation,
    }
