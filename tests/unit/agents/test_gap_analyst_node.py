from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from careervector.agents.nodes.gap_analyst_node import gap_analyst_node
from careervector.agents.schemas import SemanticGapAssessment, SkillEquivalenceNote
from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.infra.llm.client import Message

pytestmark = pytest.mark.unit

_PYTORCH = Skill(id="pytorch", name="PyTorch", category=SkillCategory.FRAMEWORK)
_TENSORFLOW = Skill(id="tensorflow", name="TensorFlow", category=SkillCategory.FRAMEWORK)
_KUBERNETES = Skill(id="kubernetes", name="Kubernetes", category=SkillCategory.TOOL)


class _FakeLLMProvider:
    def __init__(self, response: BaseModel) -> None:
        self._response = response

    async def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
    ) -> BaseModel:
        return self._response

    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]:
        return
        yield


def _make_vacancy(skill_requirements: list[SkillRequirement]) -> Vacancy:
    return Vacancy(
        title="AI Engineer",
        company="Nimbus AI",
        role_type=RoleType.AI_ENGINEERING,
        seniority=SeniorityLevel.MID,
        description="Build ML systems.",
        skill_requirements=skill_requirements,
        source="mock",
        posted_at=datetime.now(UTC),
    )


async def test_gap_analyst_skips_llm_call_when_no_gap() -> None:
    vacancy = _make_vacancy(
        [SkillRequirement(skill=_PYTORCH, importance=SkillImportance.MUST_HAVE)]
    )
    candidate = Candidate(full_name="Test", skills=[CandidateSkill(skill=_PYTORCH)])
    llm = _FakeLLMProvider(SemanticGapAssessment(equivalences=[], overall_readiness_note="unused"))

    result = await gap_analyst_node({"candidate": candidate, "vacancy": vacancy, "llm": llm})

    assert result["semantic_assessment"].equivalences == []
    assert "already covers" in result["semantic_assessment"].overall_readiness_note


async def test_gap_analyst_filters_hallucinated_skill_ids_out_of_llm_response() -> None:
    vacancy = _make_vacancy(
        [
            SkillRequirement(skill=_TENSORFLOW, importance=SkillImportance.MUST_HAVE),
            SkillRequirement(skill=_KUBERNETES, importance=SkillImportance.MUST_HAVE),
        ]
    )
    candidate = Candidate(full_name="Test", skills=[CandidateSkill(skill=_PYTORCH)])
    llm_response = SemanticGapAssessment(
        equivalences=[
            SkillEquivalenceNote(
                missing_skill_id="tensorflow",
                closest_candidate_skill_id="pytorch",
                equivalence_rationale="Deep PyTorch experience transfers directly.",
                effectively_covered=True,
            ),
            SkillEquivalenceNote(
                missing_skill_id="rust",
                closest_candidate_skill_id="pytorch",
                equivalence_rationale="hallucinated missing skill",
                effectively_covered=True,
            ),
            SkillEquivalenceNote(
                missing_skill_id="kubernetes",
                closest_candidate_skill_id="cobol",
                equivalence_rationale="hallucinated candidate skill",
                effectively_covered=True,
            ),
        ],
        overall_readiness_note="Mostly ready.",
    )
    llm = _FakeLLMProvider(llm_response)

    result = await gap_analyst_node({"candidate": candidate, "vacancy": vacancy, "llm": llm})

    assert [note.missing_skill_id for note in result["semantic_assessment"].equivalences] == [
        "tensorflow"
    ]
