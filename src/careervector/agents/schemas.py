from typing import Literal

from pydantic import BaseModel, Field


class SkillEquivalenceNote(BaseModel):
    """The gap-analyst agent's judgment on whether a candidate's existing skills are a
    credible substitute for one skill the deterministic diff flagged as missing.
    """

    missing_skill_id: str
    closest_candidate_skill_id: str | None = None
    equivalence_rationale: str
    effectively_covered: bool


class SemanticGapAssessment(BaseModel):
    """Semantic judgment layered on top of the deterministic `SkillGapReport` — never a
    replacement for it. `equivalences` only ever covers skills the deterministic diff
    already flagged as missing.
    """

    equivalences: list[SkillEquivalenceNote] = Field(default_factory=list)
    overall_readiness_note: str


class RoadmapItem(BaseModel):
    skill_id: str
    priority: Literal["high", "medium", "low"]
    rationale: str
    suggested_resources: list[str] = Field(default_factory=list)


class RoadmapOutput(BaseModel):
    """The roadmap-synthesizer agent's structured output."""

    learning_roadmap: list[RoadmapItem] = Field(default_factory=list)
    tailored_resume_bullets: list[str] = Field(default_factory=list)
    interview_prep_questions: list[str] = Field(default_factory=list)
    summary: str
