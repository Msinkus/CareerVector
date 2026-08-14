from sqlalchemy.ext.asyncio import AsyncSession

from careervector.domain.candidates.models import Candidate
from careervector.infra.db.models import CandidateORM, CandidateSkillORM


async def create_candidate(candidate: Candidate, session: AsyncSession) -> None:
    """Persists a freshly parsed candidate. Each call mints a new candidate record —
    re-parsing a resume is treated as a new profile, not an update to a prior one.
    """
    session.add(
        CandidateORM(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            summary=candidate.summary,
            total_years_experience=candidate.total_years_experience,
            target_role_type=candidate.target_role_type,
            raw_resume_text=candidate.raw_resume_text,
            created_at=candidate.created_at,
        )
    )
    for candidate_skill in candidate.skills:
        session.add(
            CandidateSkillORM(
                candidate_id=candidate.id,
                skill_id=candidate_skill.skill.id,
                years_experience=candidate_skill.years_experience,
                proficiency=candidate_skill.proficiency,
            )
        )
    await session.commit()
