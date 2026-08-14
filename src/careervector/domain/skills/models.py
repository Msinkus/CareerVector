from enum import StrEnum

from pydantic import BaseModel, Field


class SkillCategory(StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    CONCEPT = "concept"


class SkillImportance(StrEnum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class ProficiencyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    """A single node in the standardized skill taxonomy, identified by a stable slug."""

    id: str = Field(..., description="Stable slug, e.g. 'kafka', 'postgresql'")
    name: str
    category: SkillCategory


class SkillRequirement(BaseModel):
    """A skill as required by a vacancy, with its importance to the role."""

    skill: Skill
    importance: SkillImportance
    min_years_experience: int | None = None
