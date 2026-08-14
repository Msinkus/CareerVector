from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from careervector.domain.skills.models import SkillRequirement


class RoleType(StrEnum):
    BACKEND = "backend"
    DATA = "data"
    AI_ENGINEERING = "ai_engineering"


class SeniorityLevel(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"


class Vacancy(BaseModel):
    """A standardized job posting, as produced by the ingestion pipeline."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    company: str
    role_type: RoleType
    seniority: SeniorityLevel
    description: str
    skill_requirements: list[SkillRequirement] = Field(default_factory=list)
    location: str | None = None
    remote: bool = False
    source: str
    source_url: str | None = None
    posted_at: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
