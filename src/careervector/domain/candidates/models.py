from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from careervector.domain.skills.models import ProficiencyLevel, Skill
from careervector.domain.vacancies.models import RoleType


class CandidateSkill(BaseModel):
    """A skill as possessed by a candidate, parsed from their resume/profile."""

    skill: Skill
    years_experience: float | None = None
    proficiency: ProficiencyLevel | None = None


class Candidate(BaseModel):
    """A structured candidate profile, parsed once and reused across all matching."""

    id: UUID = Field(default_factory=uuid4)
    full_name: str
    email: EmailStr | None = None
    summary: str | None = None
    skills: list[CandidateSkill] = Field(default_factory=list)
    total_years_experience: float | None = None
    target_role_type: RoleType | None = None
    raw_resume_text: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
