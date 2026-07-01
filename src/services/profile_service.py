from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from ai import AIRouter
from ai.schemas.profile import CandidateProfileSchema
from ai.schemas.result import AIResult
from db.models import CandidateProfile


def _merge_profiles(base: dict, extra: dict) -> dict:
    merged = {**base}
    for key, value in extra.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list) and not value:
            continue
        merged[key] = value
    return merged


def _apply_profile_data(profile: CandidateProfile, profile_data: dict, resume_text: str, path: Path) -> None:
    salary = profile_data.get("salary_estimate") or {}
    profile.resume_raw = resume_text
    profile.resume_path = str(path)
    profile.full_name = profile_data.get("full_name")
    profile.title = profile_data.get("title")
    profile.experience_years = profile_data.get("experience_years")
    profile.skills_json = json.dumps(profile_data.get("skills", []), ensure_ascii=False)
    profile.strengths_json = json.dumps(profile_data.get("strengths", []), ensure_ascii=False)
    profile.weaknesses_json = json.dumps(profile_data.get("weaknesses", []), ensure_ascii=False)
    profile.recommended_roles_json = json.dumps(profile_data.get("recommended_roles", []), ensure_ascii=False)
    profile.salary_min = salary.get("min")
    profile.salary_max = salary.get("max")
    profile.salary_currency = salary.get("currency", "RUR")
    profile.ai_summary = profile_data.get("ai_summary")


def _find_profile_for_upsert(session: Session, path: Path) -> CandidateProfile | None:
    """Найти профиль для обновления: по resume_path, иначе последний по updated_at."""
    by_path = session.execute(
        select(CandidateProfile)
        .where(CandidateProfile.resume_path == str(path))
        .order_by(CandidateProfile.updated_at.desc())
    ).scalars().first()
    if by_path is not None:
        return by_path

    return session.execute(
        select(CandidateProfile).order_by(CandidateProfile.updated_at.desc())
    ).scalars().first()


def parse_resume_upload(
    session: Session,
    content: str,
    *,
    filename: str = "resume.md",
) -> tuple[CandidateProfile, AIResult]:
    """Сохранить загруженное резюме и распарсить через AI."""
    resumes_dir = config.ROOT / "data" / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name or "resume.md"
    if not safe_name.lower().endswith(".md"):
        safe_name = f"{safe_name}.md"
    path = resumes_dir / safe_name
    path.write_text(content, encoding="utf-8")
    return parse_resume_file(session, path)


def parse_resume_file(
    session: Session,
    resume_path: str | Path,
    *,
    upsert: bool = True,
) -> tuple[CandidateProfile, AIResult]:
    path = Path(resume_path)
    if not path.exists():
        raise FileNotFoundError(f"Резюме не найдено: {path}")

    resume_text = path.read_text(encoding="utf-8")
    router = AIRouter(session)

    parse_result = router.route(
        "parse_resume",
        {"resume_text": resume_text},
        parse_json=True,
    )
    profile_data = parse_result.parsed or {}

    try:
        ru_result = router.route(
            "analyze_resume_ru",
            {"resume_text": resume_text},
            parse_json=True,
        )
        if ru_result.parsed:
            profile_data = _merge_profiles(profile_data, ru_result.parsed)
    except Exception:
        pass

    try:
        schema = CandidateProfileSchema.model_validate(profile_data)
        profile_data = schema.model_dump()
    except ValidationError:
        profile_data = CandidateProfileSchema(
            full_name=profile_data.get("full_name", ""),
            title=profile_data.get("title", ""),
            ai_summary=profile_data.get("ai_summary", parse_result.content[:500]),
        ).model_dump()

    profile: CandidateProfile | None = None
    if upsert:
        profile = _find_profile_for_upsert(session, path)

    if profile is None:
        profile = CandidateProfile()
        session.add(profile)

    _apply_profile_data(profile, profile_data, resume_text, path)
    session.commit()
    session.refresh(profile)

    combined = AIResult(
        content=json.dumps(profile_data, ensure_ascii=False, indent=2),
        provider=parse_result.provider,
        model=parse_result.model,
        task_type="parse_resume",
        input_tokens=parse_result.input_tokens,
        output_tokens=parse_result.output_tokens,
        total_tokens=parse_result.total_tokens,
        parsed=profile_data,
        warnings=parse_result.warnings,
    )
    return profile, combined


def get_latest_profile(session: Session) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).order_by(CandidateProfile.updated_at.desc())
    ).scalars().first()
