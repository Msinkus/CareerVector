from typing import cast

from careervector.agents.prompts.roadmap_prompt import ROADMAP_SYNTHESIZER_SYSTEM_PROMPT
from careervector.agents.schemas import RoadmapOutput, SemanticGapAssessment
from careervector.agents.state import CopilotState
from careervector.domain.candidates.models import Candidate
from careervector.domain.skills.gap_analysis import SkillGapReport
from careervector.domain.vacancies.models import Vacancy
from careervector.infra.llm.client import Message


def _format_roadmap_prompt(
    candidate: Candidate,
    vacancy: Vacancy,
    gap_report: SkillGapReport,
    assessment: SemanticGapAssessment,
) -> str:
    matched = ", ".join(skill.name for skill in gap_report.matched_skills) or "(none)"
    missing_lines = [
        f"- {req.skill.id} ({req.skill.name}), must-have" for req in gap_report.missing_must_have
    ] + [
        f"- {req.skill.id} ({req.skill.name}), nice-to-have"
        for req in gap_report.missing_nice_to_have
    ]
    equivalence_lines = [
        f"- {note.missing_skill_id}: "
        f"{'effectively covered' if note.effectively_covered else 'genuine gap'} "
        f"— {note.equivalence_rationale}"
        for note in assessment.equivalences
    ] or ["(no adjacent-skill substitutes found)"]

    return (
        f"Candidate: {candidate.full_name}\n"
        f"Summary: {candidate.summary or '(none provided)'}\n\n"
        f"Target vacancy: {vacancy.title} at {vacancy.company} ({vacancy.role_type.value}, "
        f"{vacancy.seniority.value})\n"
        f"Vacancy description: {vacancy.description}\n\n"
        f"Matched skills: {matched}\n\n"
        f"Missing skills:\n{chr(10).join(missing_lines) or '(none)'}\n\n"
        f"Gap-analyst equivalence notes:\n{chr(10).join(equivalence_lines)}\n"
        f"Overall readiness note: {assessment.overall_readiness_note}"
    )


async def roadmap_synthesizer_node(state: CopilotState) -> CopilotState:
    candidate = state["candidate"]
    vacancy = state["vacancy"]
    gap_report = state["gap_report"]
    assessment = state["semantic_assessment"]

    missing_ids = {req.skill.id for req in gap_report.missing_must_have} | {
        req.skill.id for req in gap_report.missing_nice_to_have
    }

    raw_output = cast(
        RoadmapOutput,
        await state["llm"].complete(
            system=ROADMAP_SYNTHESIZER_SYSTEM_PROMPT,
            messages=[
                Message(
                    role="user",
                    content=_format_roadmap_prompt(candidate, vacancy, gap_report, assessment),
                )
            ],
            response_model=RoadmapOutput,
        ),
    )
    filtered_roadmap = [
        item for item in raw_output.learning_roadmap if item.skill_id in missing_ids
    ]

    return CopilotState(
        roadmap=RoadmapOutput(
            learning_roadmap=filtered_roadmap,
            tailored_resume_bullets=raw_output.tailored_resume_bullets,
            interview_prep_questions=raw_output.interview_prep_questions,
            summary=raw_output.summary,
        )
    )
