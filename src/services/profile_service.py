from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select, update
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


def _slug_name(display_name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", display_name.strip().lower())
    slug = re.sub(r"[\s-]+", "_", slug).strip("_")
    return slug[:48] or "profile"


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


def list_profiles(session: Session) -> list[CandidateProfile]:
    return list(
        session.execute(
            select(CandidateProfile).order_by(CandidateProfile.is_active.desc(), CandidateProfile.updated_at.desc())
        ).scalars()
    )


def get_active_profile(session: Session) -> CandidateProfile | None:
    active = session.execute(
        select(CandidateProfile).where(CandidateProfile.is_active.is_(True)).order_by(CandidateProfile.updated_at.desc())
    ).scalars().first()
    if active:
        return active
    return get_latest_profile(session)


def set_active_profile(session: Session, profile_id: int) -> CandidateProfile | None:
    profile = session.get(CandidateProfile, profile_id)
    if not profile:
        return None
    session.execute(update(CandidateProfile).values(is_active=False))
    profile.is_active = True
    session.commit()
    session.refresh(profile)
    return profile


def get_latest_profile(session: Session) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).order_by(CandidateProfile.updated_at.desc())
    ).scalars().first()


def get_profile(session: Session, profile_id: int) -> CandidateProfile | None:
    return session.get(CandidateProfile, profile_id)


def _parse_resume_text(session: Session, resume_text: str) -> tuple[dict, AIResult]:
    router = AIRouter(session)
    parse_result = router.route("parse_resume", {"resume_text": resume_text}, parse_json=True)
    profile_data = parse_result.parsed or {}
    try:
        ru_result = router.route("analyze_resume_ru", {"resume_text": resume_text}, parse_json=True)
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
    return profile_data, combined


def create_profile_from_resume(
    session: Session,
    content: str,
    *,
    display_name: str,
    filename: str = "resume.md",
) -> tuple[CandidateProfile, AIResult]:
    """Создать новый изолированный профиль резюме (не перезаписывает существующие)."""
    name = display_name.strip()
    if not name:
        raise ValueError("Укажите название профиля резюме")

    resumes_dir = config.ROOT / "data" / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name or "resume.md"
    if not safe_name.lower().endswith(".md"):
        safe_name = f"{safe_name}.md"
    path = resumes_dir / f"{_slug_name(name)}_{safe_name}"
    path.write_text(content, encoding="utf-8")

    profile_data, combined = _parse_resume_text(session, content)
    session.execute(update(CandidateProfile).values(is_active=False))

    profile = CandidateProfile(display_name=name, is_active=True)
    session.add(profile)
    _apply_profile_data(profile, profile_data, content, path)
    session.commit()
    session.refresh(profile)
    return profile, combined


def parse_resume_upload(
    session: Session,
    content: str,
    *,
    display_name: str,
    filename: str = "resume.md",
) -> tuple[CandidateProfile, AIResult]:
    return create_profile_from_resume(session, content, display_name=display_name, filename=filename)


def parse_resume_file(
    session: Session,
    resume_path: str | Path,
    *,
    display_name: str | None = None,
    upsert: bool = False,
) -> tuple[CandidateProfile, AIResult]:
    path = Path(resume_path)
    if not path.exists():
        raise FileNotFoundError(f"Резюме не найдено: {path}")
    resume_text = path.read_text(encoding="utf-8")
    label = display_name or path.stem
    if upsert:
        raise NotImplementedError("Обновление существующего профиля через parse_resume_file отключено")
    return create_profile_from_resume(session, resume_text, display_name=label, filename=path.name)
