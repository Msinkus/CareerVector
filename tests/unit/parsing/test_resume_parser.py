from collections.abc import AsyncIterator

import pytest
from pydantic import BaseModel

from careervector.domain.skills.models import ProficiencyLevel, Skill, SkillCategory
from careervector.domain.vacancies.models import RoleType
from careervector.infra.llm.client import Message
from careervector.parsing.resume_parser import parse_resume
from careervector.parsing.schemas import ExtractedCandidateProfile, ExtractedSkill

pytestmark = pytest.mark.unit

_KNOWN_SKILLS = [
    Skill(id="python", name="Python", category=SkillCategory.LANGUAGE),
    Skill(id="fastapi", name="FastAPI", category=SkillCategory.FRAMEWORK),
]


class _FakeLLMProvider:
    def __init__(self, response: ExtractedCandidateProfile) -> None:
        self._response = response

    async def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
    ) -> ExtractedCandidateProfile:
        return self._response

    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]:
        return
        yield


async def test_parse_resume_maps_known_skills_to_domain_candidate() -> None:
    extraction = ExtractedCandidateProfile(
        full_name="Priya Nair",
        email="priya@example.com",
        summary="Backend engineer.",
        skills=[
            ExtractedSkill(
                skill_id="python", years_experience=6, proficiency=ProficiencyLevel.EXPERT
            )
        ],
        total_years_experience=6,
        target_role_type=RoleType.BACKEND,
    )
    llm = _FakeLLMProvider(extraction)

    candidate = await parse_resume("raw resume text", _KNOWN_SKILLS, llm)

    assert candidate.full_name == "Priya Nair"
    assert candidate.email == "priya@example.com"
    assert candidate.raw_resume_text == "raw resume text"
    assert candidate.target_role_type == RoleType.BACKEND
    assert len(candidate.skills) == 1
    assert candidate.skills[0].skill.id == "python"
    assert candidate.skills[0].proficiency == ProficiencyLevel.EXPERT


async def test_parse_resume_drops_skills_outside_known_taxonomy() -> None:
    extraction = ExtractedCandidateProfile(
        full_name="Someone",
        skills=[ExtractedSkill(skill_id="python"), ExtractedSkill(skill_id="cobol")],
    )
    llm = _FakeLLMProvider(extraction)

    candidate = await parse_resume("text", _KNOWN_SKILLS, llm)

    assert [cs.skill.id for cs in candidate.skills] == ["python"]
