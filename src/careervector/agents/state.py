from typing import TypedDict

from careervector.agents.schemas import RoadmapOutput, SemanticGapAssessment
from careervector.domain.candidates.models import Candidate
from careervector.domain.skills.gap_analysis import SkillGapReport
from careervector.domain.skills.models import Skill
from careervector.domain.vacancies.models import Vacancy
from careervector.infra.llm.client import LLMProvider


class CopilotState(TypedDict, total=False):
    """State threaded through the copilot LangGraph: parser -> gap_analyst ->
    roadmap_synthesizer. Each node reads what earlier nodes produced and returns only the
    keys it adds, per LangGraph's partial-update node convention.
    """

    resume_text: str
    vacancy: Vacancy
    known_skills: list[Skill]
    llm: LLMProvider

    candidate: Candidate
    gap_report: SkillGapReport
    semantic_assessment: SemanticGapAssessment
    roadmap: RoadmapOutput
