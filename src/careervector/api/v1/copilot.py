from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from careervector.agents.graph import get_copilot_graph
from careervector.agents.schemas import RoadmapItem, RoadmapOutput, SemanticGapAssessment
from careervector.agents.state import CopilotState
from careervector.domain.candidates.models import Candidate
from careervector.domain.skills.gap_analysis import SkillGapReport
from careervector.domain.skills.models import SkillImportance
from careervector.domain.vacancies.models import Vacancy
from careervector.infra.db.repositories.skill_repository import list_skills
from careervector.infra.db.repositories.vacancy_repository import get_vacancy_by_id
from careervector.infra.db.session import get_session
from careervector.infra.llm.client import LLMProvider, get_llm_provider

router = APIRouter(prefix="/copilot", tags=["copilot"])


class RoadmapRequest(BaseModel):
    resume_text: str
    vacancy_id: UUID


class SkillGapItemResponse(BaseModel):
    skill_id: str
    skill_name: str
    importance: SkillImportance


class SkillEquivalenceResponse(BaseModel):
    missing_skill_id: str
    closest_candidate_skill_id: str | None
    equivalence_rationale: str
    effectively_covered: bool


class RoadmapItemResponse(BaseModel):
    skill_id: str
    priority: str
    rationale: str
    suggested_resources: list[str]

    @classmethod
    def from_domain(cls, item: RoadmapItem) -> "RoadmapItemResponse":
        return cls(
            skill_id=item.skill_id,
            priority=item.priority,
            rationale=item.rationale,
            suggested_resources=item.suggested_resources,
        )


class RoadmapResponse(BaseModel):
    candidate_full_name: str
    vacancy_id: str
    vacancy_title: str
    matched_skills: list[str]
    missing_must_have: list[SkillGapItemResponse]
    missing_nice_to_have: list[SkillGapItemResponse]
    must_have_match_ratio: float
    semantic_equivalences: list[SkillEquivalenceResponse]
    readiness_note: str
    learning_roadmap: list[RoadmapItemResponse]
    tailored_resume_bullets: list[str]
    interview_prep_questions: list[str]
    summary: str

    @classmethod
    def from_state(
        cls,
        candidate: Candidate,
        vacancy: Vacancy,
        gap_report: SkillGapReport,
        assessment: SemanticGapAssessment,
        roadmap: RoadmapOutput,
    ) -> "RoadmapResponse":
        return cls(
            candidate_full_name=candidate.full_name,
            vacancy_id=str(gap_report.vacancy_id),
            vacancy_title=vacancy.title,
            matched_skills=[skill.name for skill in gap_report.matched_skills],
            missing_must_have=[
                SkillGapItemResponse(
                    skill_id=req.skill.id, skill_name=req.skill.name, importance=req.importance
                )
                for req in gap_report.missing_must_have
            ],
            missing_nice_to_have=[
                SkillGapItemResponse(
                    skill_id=req.skill.id, skill_name=req.skill.name, importance=req.importance
                )
                for req in gap_report.missing_nice_to_have
            ],
            must_have_match_ratio=gap_report.must_have_match_ratio,
            semantic_equivalences=[
                SkillEquivalenceResponse(
                    missing_skill_id=note.missing_skill_id,
                    closest_candidate_skill_id=note.closest_candidate_skill_id,
                    equivalence_rationale=note.equivalence_rationale,
                    effectively_covered=note.effectively_covered,
                )
                for note in assessment.equivalences
            ],
            readiness_note=assessment.overall_readiness_note,
            learning_roadmap=[
                RoadmapItemResponse.from_domain(item) for item in roadmap.learning_roadmap
            ],
            tailored_resume_bullets=roadmap.tailored_resume_bullets,
            interview_prep_questions=roadmap.interview_prep_questions,
            summary=roadmap.summary,
        )


@router.post("/roadmap", response_model=RoadmapResponse)
async def generate_roadmap(
    request: RoadmapRequest,
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_llm_provider),
) -> RoadmapResponse:
    vacancy = await get_vacancy_by_id(request.vacancy_id, session)
    if vacancy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vacancy not found.")

    known_skills = await list_skills(session)

    graph = get_copilot_graph()
    result = cast(
        dict[str, Any],
        await graph.ainvoke(
            CopilotState(
                resume_text=request.resume_text,
                vacancy=vacancy,
                known_skills=known_skills,
                llm=llm,
            )
        ),
    )

    return RoadmapResponse.from_state(
        candidate=result["candidate"],
        vacancy=vacancy,
        gap_report=result["gap_report"],
        assessment=result["semantic_assessment"],
        roadmap=result["roadmap"],
    )
