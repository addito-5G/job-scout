"""AI-рекомендации по резюме под конкретную вакансию (Groq primary)."""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from ai import AIRouter
from ai.ai_router import AIRouterError
from db.models import CandidateProfile, Vacancy
from db.repositories.match_repo import get_match, save_fit_advice
from domain.role import infer_target_role
from services.cover_letter_context import profile_for_cover_letter_json
from services.match_service import compute_fit_match, vacancy_to_json


_HALLUCINATION_MARKERS = (
    "компания a",
    "иван петров",
    "предположим",
    "данные не указаны",
    "не указана явно",
    "выдуман",
)


def _resume_excerpt(profile: CandidateProfile, limit: int = 5000) -> str:
    raw = (profile.resume_raw or "").strip()
    if not raw:
        return ""
    return raw[:limit]


def _fit_context_json(match_data: dict) -> str:
    compact = {
        "match_score": match_data.get("match_score"),
        "recommendation": match_data.get("recommendation"),
        "match_summary": match_data.get("match_summary"),
        "matched_skills": (match_data.get("matched_skills") or [])[:15],
        "missing_skills": (match_data.get("missing_skills") or [])[:12],
        "gaps_to_improve": (match_data.get("gaps_to_improve") or [])[:8],
        "strengths": (match_data.get("strengths") or [])[:8],
        "risks": (match_data.get("risks") or [])[:6],
    }
    return json.dumps(compact, ensure_ascii=False)


def _parse_advice(result) -> dict:
    advice = result.parsed if result.parsed else {}
    if not isinstance(advice, dict):
        advice = {}
    if not advice and result.content:
        try:
            advice = json.loads(result.content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", result.content, re.DOTALL)
            if match:
                try:
                    advice = json.loads(match.group())
                except json.JSONDecodeError:
                    advice = {}
    return advice


def _validate_advice(advice: dict) -> tuple[bool, str]:
    verdict = (advice.get("verdict") or "").strip()
    if len(verdict) < 20:
        return False, "AI не вернул вердикт"

    readiness = advice.get("fit_readiness")
    if readiness not in ("strong", "moderate", "stretch"):
        advice["fit_readiness"] = "moderate"

    additions = advice.get("resume_additions") or []
    bullets = advice.get("resume_bullets") or []
    if not additions and not bullets:
        return False, "Нет рекомендаций по резюме"

    lower = verdict.lower()
    for marker in _HALLUCINATION_MARKERS:
        if marker in lower:
            return False, f"Подозрительная формулировка: {marker}"

    return True, ""


def _normalize_advice(advice: dict) -> dict:
    def _list(key: str, limit: int) -> list:
        raw = advice.get(key) or []
        if not isinstance(raw, list):
            return []
        return [str(x).strip() for x in raw if str(x).strip()][:limit]

    additions_raw = advice.get("resume_additions") or []
    additions: list[dict] = []
    if isinstance(additions_raw, list):
        for item in additions_raw[:6]:
            if isinstance(item, dict) and item.get("item"):
                effort = item.get("effort") or "medium"
                if effort not in ("quick", "medium", "long"):
                    effort = "medium"
                additions.append(
                    {
                        "item": str(item["item"]).strip()[:300],
                        "why": str(item.get("why") or "").strip()[:400],
                        "effort": effort,
                    }
                )

    readiness = advice.get("fit_readiness")
    if readiness not in ("strong", "moderate", "stretch"):
        readiness = "moderate"

    return {
        "verdict": (advice.get("verdict") or "").strip()[:600],
        "fit_readiness": readiness,
        "priority_action": (advice.get("priority_action") or "").strip()[:200],
        "resume_additions": additions,
        "resume_bullets": _list("resume_bullets", 5),
        "interview_talking_points": _list("interview_talking_points", 6),
        "honest_gaps": _list("honest_gaps", 5),
    }


def generate_vacancy_fit_advice(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    use_cache: bool = True,
) -> dict:
    if not profile.resume_raw and not profile.skills_json:
        raise ValueError("Загрузите резюме, чтобы получить рекомендации.")

    match_data = compute_fit_match(session, profile, vacancy)
    target_role = infer_target_role(vacancy.title)

    candidate_name = profile.full_name or profile.display_name or "Кандидат"
    payload = {
        "candidate_name": candidate_name,
        "target_role": target_role,
        "resume_excerpt": _resume_excerpt(profile),
        "profile_json": profile_for_cover_letter_json(profile, target_role=target_role),
        "vacancy_json": vacancy_to_json(session, vacancy),
        "fit_context_json": _fit_context_json(match_data),
    }

    router = AIRouter(session)
    attempts: list[tuple[bool, str | None]] = [
        (use_cache, None),
        (False, "groq"),
        (False, "yandex"),
        (False, "ollama"),
    ]
    last_error = "неизвестная ошибка"

    for cache_ok, force_provider in attempts:
        try:
            result = router.route(
                "vacancy_fit_advice",
                payload,
                parse_json=True,
                use_cache=cache_ok,
                force_provider=force_provider,
            )
        except AIRouterError as exc:
            last_error = str(exc)
            continue

        advice = _normalize_advice(_parse_advice(result))
        valid, reason = _validate_advice(advice)
        if valid:
            advice["provider"] = result.provider
            advice["match_score"] = match_data.get("match_score")
            save_fit_advice(session, vacancy.id, profile.id, advice)
            return advice
        last_error = reason

    raise ValueError(f"AI не смог подготовить рекомендации ({last_error}). Попробуйте ещё раз.")


def load_saved_fit_advice(
    session: Session,
    vacancy_id: int,
    profile_id: int,
) -> dict | None:
    row = get_match(session, vacancy_id, profile_id, "fit")
    if not row or not row.fit_advice_json:
        return None
    try:
        data = json.loads(row.fit_advice_json)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
