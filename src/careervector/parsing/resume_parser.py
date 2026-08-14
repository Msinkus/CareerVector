from typing import cast

from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.models import Skill
from careervector.infra.llm.client import LLMProvider, Message
from careervector.parsing.schemas import ExtractedCandidateProfile

_SYSTEM_PROMPT = """You are a resume parser for CareerVector, a job-market intelligence platform.
Extract a structured candidate profile from the resume text the user provides.

Only use skill_id values from this taxonomy — do not invent new ids, and omit any skill
mentioned in the resume that has no match in the list:
{skill_taxonomy}

Call the emit_result tool exactly once with the extracted profile."""


def _format_taxonomy(known_skills: list[Skill]) -> str:
    return "\n".join(f"- {skill.id}: {skill.name}" for skill in known_skills)


async def parse_resume(raw_text: str, known_skills: list[Skill], llm: LLMProvider) -> Candidate:
    """Extracts a structured Candidate profile from raw resume/markdown/plain text.

    Matching free-text skill mentions to the taxonomy is a semantic task delegated to the
    LLM, but which skill_id values are valid is enforced deterministically here — the
    model's own claim of correctness isn't trusted.
    """
    skills_by_id = {skill.id: skill for skill in known_skills}
    system = _SYSTEM_PROMPT.format(skill_taxonomy=_format_taxonomy(known_skills))

    extraction = cast(
        ExtractedCandidateProfile,
        await llm.complete(
            system=system,
            messages=[Message(role="user", content=raw_text)],
            response_model=ExtractedCandidateProfile,
        ),
    )

    candidate_skills = [
        CandidateSkill(
            skill=skills_by_id[extracted.skill_id],
            years_experience=extracted.years_experience,
            proficiency=extracted.proficiency,
        )
        for extracted in extraction.skills
        if extracted.skill_id in skills_by_id
    ]

    return Candidate(
        full_name=extraction.full_name,
        email=extraction.email,
        summary=extraction.summary,
        skills=candidate_skills,
        total_years_experience=extraction.total_years_experience,
        target_role_type=extraction.target_role_type,
        raw_resume_text=raw_text,
    )
