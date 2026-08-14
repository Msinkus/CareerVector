from uuid import UUID

from pydantic import BaseModel

from careervector.domain.candidates.models import Candidate
from careervector.domain.skills.models import Skill, SkillImportance, SkillRequirement
from careervector.domain.vacancies.models import Vacancy


class SkillGapReport(BaseModel):
    """Deterministic candidate-vs-vacancy skill comparison. Plain set-difference over
    skill ids — no LLM involved, per the deterministic/LLM-generated split in CLAUDE.md.
    """

    candidate_id: UUID
    vacancy_id: UUID
    matched_skills: list[Skill]
    missing_must_have: list[SkillRequirement]
    missing_nice_to_have: list[SkillRequirement]
    must_have_match_ratio: float


def compute_skill_gap(candidate: Candidate, vacancy: Vacancy) -> SkillGapReport:
    candidate_skill_ids = {cs.skill.id for cs in candidate.skills}

    must_haves = [
        req for req in vacancy.skill_requirements if req.importance == SkillImportance.MUST_HAVE
    ]
    nice_to_haves = [
        req
        for req in vacancy.skill_requirements
        if req.importance == SkillImportance.NICE_TO_HAVE
    ]

    matched_skills = [
        req.skill for req in vacancy.skill_requirements if req.skill.id in candidate_skill_ids
    ]
    missing_must_have = [req for req in must_haves if req.skill.id not in candidate_skill_ids]
    missing_nice_to_have = [
        req for req in nice_to_haves if req.skill.id not in candidate_skill_ids
    ]

    must_have_match_ratio = (
        (len(must_haves) - len(missing_must_have)) / len(must_haves) if must_haves else 1.0
    )

    return SkillGapReport(
        candidate_id=candidate.id,
        vacancy_id=vacancy.id,
        matched_skills=matched_skills,
        missing_must_have=missing_must_have,
        missing_nice_to_have=missing_nice_to_have,
        must_have_match_ratio=must_have_match_ratio,
    )
