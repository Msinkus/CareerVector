from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from careervector.agents.graph import build_copilot_graph
from careervector.agents.schemas import (
    RoadmapItem,
    RoadmapOutput,
    SemanticGapAssessment,
    SkillEquivalenceNote,
)
from careervector.agents.state import CopilotState
from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.infra.llm.client import Message
from careervector.parsing.schemas import ExtractedCandidateProfile, ExtractedSkill

pytestmark = pytest.mark.unit

_PYTHON = Skill(id="python", name="Python", category=SkillCategory.LANGUAGE)
_KUBERNETES = Skill(id="kubernetes", name="Kubernetes", category=SkillCategory.TOOL)


class _ScriptedLLMProvider:
    """Dispatches by response_model so the full compiled graph can be exercised without a
    real Claude call — one canned response per node's structured-output type.
    """

    def __init__(self) -> None:
        self._responses: dict[type[BaseModel], BaseModel] = {
            ExtractedCandidateProfile: ExtractedCandidateProfile(
                full_name="Priya Nair",
                skills=[ExtractedSkill(skill_id="python")],
            ),
            SemanticGapAssessment: SemanticGapAssessment(
                equivalences=[
                    SkillEquivalenceNote(
                        missing_skill_id="kubernetes",
                        closest_candidate_skill_id=None,
                        equivalence_rationale="No adjacent experience.",
                        effectively_covered=False,
                    )
                ],
                overall_readiness_note="Needs Kubernetes experience.",
            ),
            RoadmapOutput: RoadmapOutput(
                learning_roadmap=[
                    RoadmapItem(
                        skill_id="kubernetes",
                        priority="high",
                        rationale="Required for the role.",
                        suggested_resources=["Kubernetes docs"],
                    )
                ],
                tailored_resume_bullets=["Built Python services."],
                interview_prep_questions=["How do you deploy a service to Kubernetes?"],
                summary="Learn Kubernetes to close the main gap.",
            ),
        }

    async def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
    ) -> BaseModel:
        assert response_model is not None
        return self._responses[response_model]

    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]:
        return
        yield


async def test_full_copilot_graph_wires_parser_gap_analyst_roadmap_synthesizer() -> None:
    vacancy = Vacancy(
        title="Backend Engineer",
        company="Nimbus Systems",
        role_type=RoleType.BACKEND,
        seniority=SeniorityLevel.MID,
        description="Build things.",
        skill_requirements=[
            SkillRequirement(skill=_PYTHON, importance=SkillImportance.MUST_HAVE),
            SkillRequirement(skill=_KUBERNETES, importance=SkillImportance.MUST_HAVE),
        ],
        source="mock",
        posted_at=datetime.now(UTC),
    )
    graph = build_copilot_graph()

    result = await graph.ainvoke(
        CopilotState(
            resume_text="Priya Nair, Python backend engineer.",
            vacancy=vacancy,
            known_skills=[_PYTHON, _KUBERNETES],
            llm=_ScriptedLLMProvider(),
        )
    )

    assert result["candidate"].full_name == "Priya Nair"
    assert [req.skill.id for req in result["gap_report"].missing_must_have] == ["kubernetes"]
    assert result["semantic_assessment"].overall_readiness_note == "Needs Kubernetes experience."
    assert [item.skill_id for item in result["roadmap"].learning_roadmap] == ["kubernetes"]
    assert result["roadmap"].summary == "Learn Kubernetes to close the main gap."
