"""ORM-модели SQLite."""

from __future__ import annotations

from datetime import datetime

from time_utils import utc_now

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return utc_now()


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_company_source_external"),
        Index("idx_companies_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    name_short: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(512))
    logo_url: Mapped[str | None] = mapped_column(String(1024))
    industry: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[str | None] = mapped_column(String(64))
    rating: Mapped[float | None] = mapped_column(Float)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="company_rel")


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (Index("idx_locations_city", "city"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_full: Mapped[str | None] = mapped_column(String(512))
    country: Mapped[str] = mapped_column(String(64), default="Россия")
    region: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_remote_capital: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="location_rel")


class Vacancy(Base):
    __tablename__ = "vacancies"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_vacancy_source_external"),
        Index("idx_vacancies_published", "published_at"),
        Index("idx_vacancies_salary", "salary_from", "salary_to"),
        Index("idx_vacancies_format", "work_format"),
        Index("idx_vacancies_status", "status", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    external_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_normalized: Mapped[str | None] = mapped_column(String(512))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    department: Mapped[str | None] = mapped_column(String(255))

    description_short: Mapped[str | None] = mapped_column(Text)
    description_full: Mapped[str | None] = mapped_column(Text)
    description_raw: Mapped[str | None] = mapped_column(Text)

    salary_from: Mapped[int | None] = mapped_column(Integer)
    salary_to: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(16), default="RUR")
    salary_gross: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_text: Mapped[str | None] = mapped_column(String(255))

    work_format: Mapped[str | None] = mapped_column(String(32))
    work_format_raw: Mapped[str | None] = mapped_column(String(128))
    schedule: Mapped[str | None] = mapped_column(String(64))
    employment: Mapped[str | None] = mapped_column(String(128))

    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    location_text: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(512))

    experience_required: Mapped[str | None] = mapped_column(String(64))
    experience_years_min: Mapped[int | None] = mapped_column(Integer)
    experience_years_max: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(32), default="active")
    user_status: Mapped[str] = mapped_column(String(32), default="new")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at_source: Mapped[datetime | None] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime)

    rule_score: Mapped[int] = mapped_column(Integer, default=0)
    rule_score_reasons: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[str | None] = mapped_column(Text)

    search_settings_id: Mapped[int | None] = mapped_column(ForeignKey("search_settings.id"))
    profile_role: Mapped[str | None] = mapped_column(String(64), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    company_rel: Mapped["Company | None"] = relationship(back_populates="vacancies")
    location_rel: Mapped["Location | None"] = relationship(back_populates="vacancies")
    vacancy_skills: Mapped[list["VacancySkill"]] = relationship(back_populates="vacancy", cascade="all, delete-orphan")
    tags: Mapped[list["VacancyTag"]] = relationship(back_populates="vacancy", cascade="all, delete-orphan")
    matches: Mapped[list["VacancyMatch"]] = relationship(back_populates="vacancy")


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (Index("idx_skills_category", "category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name_normalized: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(64))
    is_hard_skill: Mapped[bool] = mapped_column(Boolean, default=True)
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vacancy_skills: Mapped[list["VacancySkill"]] = relationship(back_populates="skill")


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"
    __table_args__ = (UniqueConstraint("vacancy_id", "skill_id", name="uq_vacancy_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="vacancy_skills")
    skill: Mapped["Skill"] = relationship(back_populates="vacancy_skills")


class VacancyTag(Base):
    __tablename__ = "vacancy_tags"
    __table_args__ = (UniqueConstraint("vacancy_id", "tag", "tag_type", name="uq_vacancy_tag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)
    tag_type: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="tags")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_path: Mapped[str | None] = mapped_column(String(1024), unique=True)
    resume_raw: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    title_normalized: Mapped[str | None] = mapped_column(String(255))
    experience_years: Mapped[int | None] = mapped_column(Integer)
    experience_summary: Mapped[str | None] = mapped_column(Text)
    skills_json: Mapped[str | None] = mapped_column(Text)
    domains_json: Mapped[str | None] = mapped_column(Text)
    strengths_json: Mapped[str | None] = mapped_column(Text)
    weaknesses_json: Mapped[str | None] = mapped_column(Text)
    recommended_roles_json: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(16), default="RUR")
    work_formats_json: Mapped[str | None] = mapped_column(Text)
    locations_json: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    search_settings: Mapped[list["SearchSettings"]] = relationship(back_populates="profile")
    matches: Mapped[list["VacancyMatch"]] = relationship(back_populates="profile")


class SearchSettings(Base):
    __tablename__ = "search_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), nullable=False)
    desired_titles_json: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(16), default="RUR")
    keywords_include_json: Mapped[str | None] = mapped_column(Text)
    keywords_exclude_json: Mapped[str | None] = mapped_column(Text)
    required_skills_json: Mapped[str | None] = mapped_column(Text)
    experience_filter: Mapped[str | None] = mapped_column(String(64))
    work_formats_json: Mapped[str | None] = mapped_column(Text)
    locations_json: Mapped[str | None] = mapped_column(Text)
    employment_types_json: Mapped[str | None] = mapped_column(Text)
    ai_suggestions_json: Mapped[str | None] = mapped_column(Text)
    hh_queries_json: Mapped[str | None] = mapped_column(Text)
    habr_queries_json: Mapped[str | None] = mapped_column(Text)
    geekjob_queries_json: Mapped[str | None] = mapped_column(Text)
    profile_label: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="search_settings")


class VacancyMatch(Base):
    __tablename__ = "vacancy_matches"
    __table_args__ = (
        UniqueConstraint("vacancy_id", "profile_id", "match_level", name="uq_vacancy_match"),
        Index("idx_vacancy_matches_score", "match_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float)
    match_level: Mapped[str] = mapped_column(String(16), default="fast")
    matched_skills_json: Mapped[str | None] = mapped_column(Text)
    missing_skills_json: Mapped[str | None] = mapped_column(Text)
    strengths_for_vacancy_json: Mapped[str | None] = mapped_column(Text)
    risks_json: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(String(32))
    recommendation_reason: Mapped[str | None] = mapped_column(Text)
    ai_analysis: Mapped[str | None] = mapped_column(Text)
    cover_letter_draft: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(32))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="matches")
    profile: Mapped["CandidateProfile"] = relationship(back_populates="matches")


class AICache(Base):
    __tablename__ = "ai_cache"
    __table_args__ = (Index("idx_ai_cache_task", "task_type", "provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    response: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)


class AIUsageLog(Base):
    __tablename__ = "ai_usage_log"
    __table_args__ = (Index("idx_ai_usage_created", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    vacancy_id: Mapped[int | None] = mapped_column(ForeignKey("vacancies.id"))
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_profiles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ScanRun(Base):
    __tablename__ = "scan_runs"
    __table_args__ = (Index("idx_scan_runs_date", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    total_found: Mapped[int] = mapped_column(Integer, default=0)
    new_added: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    hh_found: Mapped[int] = mapped_column(Integer, default=0)
    habr_found: Mapped[int] = mapped_column(Integer, default=0)
    geekjob_found: Mapped[int] = mapped_column(Integer, default=0)
    search_settings_id: Mapped[int | None] = mapped_column(ForeignKey("search_settings.id"))
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_profiles.id"))
    status: Mapped[str] = mapped_column(String(32), default="running")
    error_log: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_date: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    total_vacancies: Mapped[int | None] = mapped_column(Integer)
    new_7d: Mapped[int | None] = mapped_column(Integer)
    new_30d: Mapped[int | None] = mapped_column(Integer)
    fit_count: Mapped[int | None] = mapped_column(Integer)
    not_fit_count: Mapped[int | None] = mapped_column(Integer)
    avg_match_score: Mapped[float | None] = mapped_column(Float)
    median_salary_all: Mapped[float | None] = mapped_column(Float)
    median_salary_fit: Mapped[float | None] = mapped_column(Float)
    top_skills: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
