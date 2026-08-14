from pydantic import BaseModel, EmailStr, Field

from careervector.domain.skills.models import ProficiencyLevel
from careervector.domain.vacancies.models import RoleType


class ExtractedSkill(BaseModel):
    """One skill mention extracted from resume text, before mapping to the canonical taxonomy."""

    skill_id: str
    years_experience: float | None = None
    proficiency: ProficiencyLevel | None = None


class ExtractedCandidateProfile(BaseModel):
    """The LLM's structured extraction from raw resume/profile text.

    skill_id values are constrained by the prompt to the known taxonomy passed in;
    resume_parser drops any skill_id that doesn't match a known skill rather than
    trusting the model to have stayed in-bounds.
    """

    full_name: str
    email: EmailStr | None = None
    summary: str | None = None
    skills: list[ExtractedSkill] = Field(default_factory=list)
    total_years_experience: float | None = None
    target_role_type: RoleType | None = None
