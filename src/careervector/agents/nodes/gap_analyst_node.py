from typing import cast

from careervector.agents.prompts.gap_analyst_prompt import GAP_ANALYST_SYSTEM_PROMPT
from careervector.agents.schemas import SemanticGapAssessment
from careervector.agents.state import CopilotState
from careervector.domain.candidates.models import Candidate
from careervector.domain.skills.gap_analysis import SkillGapReport, compute_skill_gap
from careervector.infra.llm.client import Message


def _format_gap_prompt(candidate: Candidate, gap_report: SkillGapReport) -> str:
    candidate_skills = (
        "\n".join(
            f"- {cs.skill.id} ({cs.skill.name}): "
            f"{cs.proficiency.value if cs.proficiency else 'unknown proficiency'}, "
            f"{cs.years_experience if cs.years_experience is not None else 'unknown'} years"
            for cs in candidate.skills
        )
        or "(none listed)"
    )
    missing_lines = [
        f"- {req.skill.id} ({req.skill.name}), must-have" for req in gap_report.missing_must_have
    ] + [
        f"- {req.skill.id} ({req.skill.name}), nice-to-have"
        for req in gap_report.missing_nice_to_have
    ]
    return (
        f"Candidate's current skills:\n{candidate_skills}\n\n"
        f"Skills the vacancy requires that the candidate does not list:\n"
        f"{chr(10).join(missing_lines)}"
    )


async def gap_analyst_node(state: CopilotState) -> CopilotState:
    candidate = state["candidate"]
    vacancy = state["vacancy"]
    gap_report = compute_skill_gap(candidate, vacancy)

    missing_ids = {req.skill.id for req in gap_report.missing_must_have} | {
        req.skill.id for req in gap_report.missing_nice_to_have
    }
    if not missing_ids:
        return CopilotState(
            gap_report=gap_report,
            semantic_assessment=SemanticGapAssessment(
                equivalences=[],
                overall_readiness_note=(
                    "Candidate already covers every required and preferred skill."
                ),
            ),
        )

    candidate_skill_ids = {cs.skill.id for cs in candidate.skills}
    raw_assessment = cast(
        SemanticGapAssessment,
        await state["llm"].complete(
            system=GAP_ANALYST_SYSTEM_PROMPT,
            messages=[Message(role="user", content=_format_gap_prompt(candidate, gap_report))],
            response_model=SemanticGapAssessment,
        ),
    )
    filtered_equivalences = [
        note
        for note in raw_assessment.equivalences
        if note.missing_skill_id in missing_ids
        and (
            note.closest_candidate_skill_id is None
            or note.closest_candidate_skill_id in candidate_skill_ids
        )
    ]

    return CopilotState(
        gap_report=gap_report,
        semantic_assessment=SemanticGapAssessment(
            equivalences=filtered_equivalences,
            overall_readiness_note=raw_assessment.overall_readiness_note,
        ),
    )
