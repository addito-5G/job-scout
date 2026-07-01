from __future__ import annotations

from pydantic import BaseModel, Field


class SalaryEstimate(BaseModel):
    min: int | None = None
    max: int | None = None
    currency: str = "RUR"
    confidence: str = "medium"


class WorkPreferences(BaseModel):
    formats: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    employment: list[str] = Field(default_factory=list)


class SearchSuggestions(BaseModel):
    keywords_include: list[str] = Field(default_factory=list)
    keywords_exclude: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    experience_filter: str = "3+"


class CandidateProfileSchema(BaseModel):
    full_name: str = ""
    title: str = ""
    experience_years: int = 0
    skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_roles: list[str] = Field(default_factory=list)
    salary_estimate: SalaryEstimate = Field(default_factory=SalaryEstimate)
    domains: list[str] = Field(default_factory=list)
    work_preferences: WorkPreferences = Field(default_factory=WorkPreferences)
    ai_summary: str = ""
    search_suggestions: SearchSuggestions = Field(default_factory=SearchSuggestions)
