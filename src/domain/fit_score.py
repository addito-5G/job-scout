"""Единый детерминированный Fit Score профиля и вакансии.

Методология (v2)
----------------
Взвешенный скор 0–100 без LLM (стабильный ранжировщик). LLM-advice — отдельно.

Компоненты:
  skills 45%  — покрытие требований с весами must / nice
  role   25%  — пересечение роли (title + recommended_roles) с вакансией
  exp    15%  — годы опыта vs expectation HH
  domain 10%  — домены профиля в тексте вакансии
  evidence 5% — strengths/summary подтверждают закрытые must-have

Must-have:
  - явные keySkills вакансии
  - термины в предложениях с «обязательно / требуется / must / необходим…»
  - сильные ролевые токены из title

Nice-to-have:
  - термины из остального description
  - фразы «будет плюсом / желательно / nice to have…»

Штрафы:
  - must coverage < 40% → −12…−22
  - must coverage == 0 при ≥2 must → потолок 48
  - ≥4 missing при низком skill_score → −6

Пороги recommendation: apply ≥72, improve_resume ≥50, иначе skip.
"""

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
        "full",
        "time",
        "part",
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
            "head of product",
            "cpo",
        }
    ),
    "sql": frozenset(
        {
            "sql",
            "postgresql",
            "postgres",
            "mysql",
            "clickhouse",
            "click house",
            "bigquery",
            "snowflake",
        }
    ),
    "python": frozenset({"python", "py"}),
    "agile": frozenset({"agile", "scrum", "kanban", "jira"}),
    "unit economics": frozenset(
        {
            "unit economics",
            "unit economic",
            "ltv",
            "cac",
            "arppu",
            "unit-экономика",
            "юнит-экономика",
            "юнит экономика",
        }
    ),
    "discovery": frozenset(
        {
            "discovery",
            "custdev",
            "customer development",
            "jtbd",
            "jobs to be done",
            "гипотез",
            "hypothesis",
            "hypothesis testing",
        }
    ),
    "roadmap": frozenset({"roadmap", "дорожная карта", "бэклог", "backlog", "приоритизац"}),
    "analytics": frozenset(
        {
            "analytics",
            "аналитика",
            "data-driven",
            "метрики",
            "metrics",
            "a/b",
            "ab test",
            "ab-тест",
            "ab тест",
            "воронк",
            "datalens",
            "tableau",
            "power bi",
            "amplitude",
            "mixpanel",
        }
    ),
    "growth": frozenset(
        {"growth", "growth hacking", "ретеншн", "retention", "acquisition", "аквизишн"}
    ),
    "ux": frozenset({"ux", "ux test", "ux-тест", "ux тесты", "usability", "юзабилити"}),
    "design": frozenset({"design", "дизайн", "ui", "figma"}),
    "ai": frozenset(
        {
            "ai",
            "ml",
            "machine learning",
            "искусственный интеллект",
            "нейросет",
            "llm",
            "gpt",
        }
    ),
    "stakeholder": frozenset(
        {"stakeholder", "стейкхолдер", "stakeholder management", "кросс-функцион"}
    ),
    "gtm": frozenset({"gtm", "go-to-market", "go to market", "вывод на рынок"}),
    "p&l": frozenset({"p&l", "pnl", "p/l", "profit and loss", "юнит-экономик"}),
    "b2b": frozenset({"b2b", "b2b saas", "saas"}),
    "b2c": frozenset({"b2c", "c2c", "marketplace"}),
    "ecommerce": frozenset({"e-commerce", "ecommerce", "ecom", "ритейл", "retail"}),
    "fintech": frozenset({"fintech", "финтех", "банк", "payments"}),
    "miro": frozenset({"miro", "figjam"}),
    "backend": frozenset(
        {"backend", "django", "fastapi", "flask", "kubernetes", "k8s", "microservices", "microservice"}
    ),
    "java": frozenset({"java", "spring", "kotlin"}),
    "mvp": frozenset({"mvp", "poc", "prototype"}),
}

DESCRIPTION_TERMS_RE = re.compile(
    r"(?:"
    r"\b(?:sql|python|postgresql|postgres|mysql|clickhouse|bigquery|"
    r"agile|scrum|kanban|jira|miro|custdev|discovery|roadmap|backlog|"
    r"a/?b(?:[- ]?tests?)?|ux|ui|figma|fintech|saas|b2b|b2c|growth|"
    r"ai|ml|llm|unit[- ]economics|stakeholder|gtm|mvp|analytics|"
    r"datalens|tableau|amplitude|mixpanel|retention|ltv|cac|arppu|"
    r"django|kubernetes|k8s|fastapi|java|spring)\b"
    r"|юнит[- ]?экономик\w*|гипотез\w*|воронк\w*|метрик\w*|продукт\w*|"
    r"приоритизац\w*|кросс[- ]?функцион\w*|продакт(?:[- ]менеджер)?|"
    r"дорожн\w*\s+карт\w*|бэклог\w*|ритейл\w*|e-?commerce)"
    ,
    re.IGNORECASE,
)

MUST_HINT_RE = re.compile(
    r"(обязательн|требуется|требуется опыт|must[- ]have|required|"
    r"необходим|ждем|ждём|ищем с опытом|ключев(ые|ой)|hard skills|"
    r"требования:|ожидаем|нужен опыт|нужны навыки)",
    re.IGNORECASE,
)
NICE_HINT_RE = re.compile(
    r"(будет плюсом|желательн|nice[- ]to[- ]have|приветству|"
    r"prefer|бонусом|хорошо если|как преимущество)",
    re.IGNORECASE,
)

WEIGHT_MUST = 3.0
WEIGHT_TITLE = 2.0
WEIGHT_NICE = 1.0

EXPERIENCE_MIN_YEARS: dict[str, int] = {
    "без опыта": 0,
    "менее 1 года": 0,
    "от 1 до 3 лет": 1,
    "от 3 до 6 лет": 3,
    "более 6 лет": 6,
}


@dataclass
class WeightedReq:
    label: str
    weight: float
    kind: str  # must | nice | title


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


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]


def _terms_in_text(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in DESCRIPTION_TERMS_RE.finditer(text or ""):
        raw = match.group(0).strip()
        key = _skill_canonical(raw) or _normalize(raw)
        if key in seen:
            continue
        seen.add(key)
        found.append(raw)
    return found


def _extract_weighted_requirements(
    *,
    title: str,
    description: str,
    vacancy_skills: list[str],
) -> list[WeightedReq]:
    """Build weighted requirement list (must > title > nice)."""
    by_key: dict[str, WeightedReq] = {}

    def upsert(label: str, weight: float, kind: str) -> None:
        clean = label.strip()
        if not clean:
            return
        key = _skill_canonical(clean) or _normalize(clean)
        if len(key) < 2:
            return
        prev = by_key.get(key)
        if prev is None or weight > prev.weight:
            by_key[key] = WeightedReq(label=clean, weight=weight, kind=kind)

    for skill in vacancy_skills:
        upsert(str(skill), WEIGHT_MUST, "must")

    for sentence in _split_sentences(description or ""):
        terms = _terms_in_text(sentence)
        if not terms:
            continue
        if MUST_HINT_RE.search(sentence):
            w, kind = WEIGHT_MUST, "must"
        elif NICE_HINT_RE.search(sentence):
            w, kind = WEIGHT_NICE, "nice"
        else:
            w, kind = WEIGHT_NICE, "nice"
        for term in terms:
            upsert(term, w, kind)

    title_tokens = _tokenize_title(title)
    role_hints = {
        "manager",
        "analyst",
        "owner",
        "engineer",
        "developer",
        "growth",
        "product",
        "продукт",
        "продакт",
    }
    for token in title_tokens:
        if token in role_hints or token in SKILL_GROUPS or _skill_canonical(token) in SKILL_GROUPS:
            upsert(token, WEIGHT_TITLE, "title")

    if not by_key and title:
        for token in sorted(title_tokens)[:6]:
            upsert(token, WEIGHT_TITLE, "title")

    # Prefer must/title first, then nice; cap noise.
    ordered = sorted(
        by_key.values(),
        key=lambda r: (-r.weight, r.kind != "must", r.label.lower()),
    )
    return ordered[:24]


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
        for term in _terms_in_text(strength):
            add(term)

    blob = " ".join(filter(None, [ai_summary, experience_summary]))
    for term in _terms_in_text(blob):
        add(term)

    return caps


def _match_weighted(
    requirements: list[WeightedReq],
    capabilities: list[str],
) -> tuple[list[str], list[str], float, float]:
    """Return matched labels, missing labels, skill_score 0..1, must_coverage 0..1."""
    matched: list[str] = []
    missing: list[str] = []
    matched_w = 0.0
    total_w = 0.0
    must_matched_w = 0.0
    must_total_w = 0.0

    for req in requirements:
        total_w += req.weight
        if req.kind == "must":
            must_total_w += req.weight
        hit = any(_skills_equivalent(req.label, cap) for cap in capabilities)
        if hit:
            matched.append(req.label)
            matched_w += req.weight
            if req.kind == "must":
                must_matched_w += req.weight
        else:
            missing.append(req.label)

    skill_score = (matched_w / total_w) if total_w else 0.0
    must_coverage = (must_matched_w / must_total_w) if must_total_w else 1.0
    return matched, missing, skill_score, must_coverage


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
        ratio = max(ratio, 0.88)
    if "growth" in vac_canonical and (
        "growth" in prof_canonical or "product manager" in prof_canonical
    ):
        ratio = max(ratio, 0.72)
    if "backend" in vac_canonical or "java" in vac_canonical:
        if "product manager" in prof_canonical and "backend" not in prof_canonical:
            ratio = min(ratio, 0.25)

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
    if years >= max(0, required - 1):
        return 0.8
    if years >= max(0, required - 2):
        return 0.62
    if years >= 1 and required <= 3:
        return 0.45
    return 0.2


def _domain_fit_score(domains: list[str], description: str, vacancy_title: str) -> float:
    if not domains:
        return 0.5
    blob = _normalize(f"{description} {vacancy_title}")
    hits = 0
    for d in domains:
        dn = _normalize(str(d))
        if not dn:
            continue
        if dn in blob:
            hits += 1
            continue
        # token / synonym group hit
        canon = _skill_canonical(dn)
        if canon and canon in blob:
            hits += 1
            continue
        parts = [p for p in dn.replace("-", " ").split() if len(p) >= 4]
        if parts and all(p in blob for p in parts[:2]):
            hits += 1
    return min(1.0, hits / max(1, min(len(domains), 3)))


def _evidence_score(
    matched: list[str],
    strengths: list[str],
    ai_summary: str | None,
    experience_summary: str | None,
) -> float:
    if not matched:
        return 0.35
    blob = _normalize(
        " ".join(filter(None, [*strengths, ai_summary or "", experience_summary or ""]))
    )
    if not blob:
        return 0.4
    hits = sum(1 for m in matched[:8] if _normalize(m) in blob or (_skill_canonical(m) or "") in blob)
    return min(1.0, 0.35 + hits * 0.12)


def _recommendation_for_score(score: int) -> str:
    if score >= 72:
        return "apply"
    if score >= 50:
        return "improve_resume"
    return "skip"


def _build_gaps(missing: list[str], *, must_missing: list[str]) -> list[str]:
    tips: list[str] = []
    for item in must_missing[:4]:
        tips.append(f"Усилить обязательное требование: {item}")
    for item in missing:
        if item in must_missing:
            continue
        if len(tips) >= 6:
            break
        tips.append(f"Усилить в резюме и опыте: {item}")
    return tips


def _build_strengths(
    matched: list[str],
    strengths: list[str],
    vacancy_title: str,
) -> list[str]:
    result: list[str] = []
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
    *,
    must_missing: list[str],
    must_coverage: float,
) -> list[str]:
    risks: list[str] = []
    if must_missing:
        risks.append(
            "Не закрыты обязательные требования: " + ", ".join(must_missing[:3])
        )
    elif must_coverage < 0.5:
        risks.append("Слабое покрытие обязательных требований вакансии")

    for item in missing[:2]:
        tip = f"Нет явного подтверждения: {item}"
        if tip not in risks:
            risks.append(tip)

    for w in weaknesses[:2]:
        if w and w not in risks:
            risks.append(w)

    if required_label and profile_years is not None:
        req_years = _experience_fit_score(profile_years, required_label)
        if req_years < 0.65:
            risks.append(
                f"Опыт {profile_years} лет может выглядеть слабее ожидания «{required_label}»"
            )

    return risks[:5]


def _build_summary(
    score: int,
    vacancy_title: str,
    matched: list[str],
    missing: list[str],
    total_reqs: int,
    *,
    must_coverage: float,
    must_total: int,
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

    must_part = ""
    if must_total:
        must_part = f" Обязательные навыки закрыты на {int(round(must_coverage * 100))}%."

    gap = ""
    if missing:
        gap = f" Стоит усилить: {', '.join(missing[:3])}."
    return (
        f"{tone} с «{vacancy_title}»: закрыто {covered} из {total_reqs} требований "
        f"({score}%).{must_part}{gap}"
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
    requirements = _extract_weighted_requirements(
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

    matched, missing, skill_score, must_coverage = _match_weighted(requirements, capabilities)
    total_reqs = len(requirements)
    must_reqs = [r for r in requirements if r.kind == "must"]
    must_missing = [
        r.label
        for r in must_reqs
        if not any(_skills_equivalent(r.label, cap) for cap in capabilities)
    ]

    if not total_reqs:
        skill_score = _role_fit_score(vacancy_title, profile_title, profile_recommended_roles)

    role_score = _role_fit_score(vacancy_title, profile_title, profile_recommended_roles)
    exp_score = _experience_fit_score(profile_experience_years, vacancy_experience_required)
    domain_score = _domain_fit_score(profile_domains, vacancy_description, vacancy_title)
    evidence = _evidence_score(
        matched,
        profile_strengths,
        profile_ai_summary,
        profile_experience_summary,
    )

    raw = (
        skill_score * 45.0
        + role_score * 25.0
        + exp_score * 15.0
        + domain_score * 10.0
        + evidence * 5.0
    )

    if must_reqs and must_coverage < 0.4:
        raw -= 12.0 + (0.4 - must_coverage) * 25.0
    if len(missing) >= 4 and skill_score < 0.45:
        raw -= 6.0
    if total_reqs >= 5 and skill_score >= 0.7 and must_coverage >= 0.6:
        raw += min(6.0, skill_score * 4.0)

    score = int(max(0, min(100, round(raw))))

    # Soft floors only when must-haves are reasonably covered.
    if must_coverage >= 0.5:
        if role_score >= 0.7 and score < 45:
            score = 45
        if skill_score >= 0.6 and score < 55:
            score = max(score, 55)
        if skill_score >= 0.75 and role_score >= 0.5 and score < 68:
            score = max(score, 68)

    if must_reqs and len(must_reqs) >= 2 and must_coverage <= 0.0:
        score = min(score, 48)

    # Strong role mismatch should not look like a good fit.
    if role_score <= 0.3 and skill_score < 0.55:
        score = min(score, 52)

    recommendation = _recommendation_for_score(score)
    gaps = _build_gaps(missing, must_missing=must_missing)
    strengths = _build_strengths(matched, profile_strengths, vacancy_title)
    risks = _build_risks(
        missing,
        profile_weaknesses,
        profile_experience_years,
        vacancy_experience_required,
        must_missing=must_missing,
        must_coverage=must_coverage,
    )
    summary = _build_summary(
        score,
        vacancy_title,
        matched,
        missing,
        total_reqs,
        must_coverage=must_coverage,
        must_total=len(must_reqs),
    )

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
