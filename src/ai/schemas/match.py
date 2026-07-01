from __future__ import annotations

from pydantic import BaseModel, Field


class VacancyMatchSchema(BaseModel):
    match_score: int = Field(ge=0, le=100)
    match_summary: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: str = "skip"
    deep_analysis: str = ""
