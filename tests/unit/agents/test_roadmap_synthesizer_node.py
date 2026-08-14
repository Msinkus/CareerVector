from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from careervector.agents.nodes.roadmap_synthesizer_node import roadmap_synthesizer_node
from careervector.agents.schemas import RoadmapItem, RoadmapOutput, SemanticGapAssessment
from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.gap_analysis import compute_skill_gap
from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.infra.llm.client import Message

pytestmark = pytest.mark.unit

_PYTHON = Skill(id="python", name="Python", category=SkillCategory.LANGUAGE)
_KAFKA = Skill(id="kafka", name="Kafka", category=SkillCategory.TOOL)


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


def _make_vacancy() -> Vacancy:
    return Vacancy(
        title="Backend Engineer",
        company="Nimbus Systems",
        role_type=RoleType.BACKEND,
        seniority=SeniorityLevel.MID,
        description="Build things.",
        skill_requirements=[SkillRequirement(skill=_KAFKA, importance=SkillImportance.MUST_HAVE)],
        source="mock",
        posted_at=datetime.now(UTC),
    )


async def test_roadmap_drops_items_for_skills_that_are_not_actually_missing() -> None:
    vacancy = _make_vacancy()
    candidate = Candidate(full_name="Test", skills=[CandidateSkill(skill=_PYTHON)])
    gap_report = compute_skill_gap(candidate, vacancy)
    assessment = SemanticGapAssessment(equivalences=[], overall_readiness_note="Needs Kafka.")

    llm_response = RoadmapOutput(
        learning_roadmap=[
            RoadmapItem(
                skill_id="kafka",
                priority="high",
                rationale="Core requirement.",
                suggested_resources=["Kafka docs"],
            ),
            RoadmapItem(
                skill_id="python",
                priority="low",
                rationale="hallucinated — candidate already has this",
                suggested_resources=[],
            ),
        ],
        tailored_resume_bullets=["Built event-driven services."],
        interview_prep_questions=["How would you design a Kafka consumer group?"],
        summary="Focus on Kafka.",
    )
    llm = _FakeLLMProvider(llm_response)

    result = await roadmap_synthesizer_node(
        {
            "candidate": candidate,
            "vacancy": vacancy,
            "gap_report": gap_report,
            "semantic_assessment": assessment,
            "llm": llm,
        }
    )

    assert [item.skill_id for item in result["roadmap"].learning_roadmap] == ["kafka"]
    assert result["roadmap"].summary == "Focus on Kafka."
