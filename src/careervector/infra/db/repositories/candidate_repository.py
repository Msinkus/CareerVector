from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.models import Skill
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


async def get_candidate_by_id(candidate_id: UUID, session: AsyncSession) -> Candidate | None:
    result = await session.execute(
        select(CandidateORM)
        .where(CandidateORM.id == candidate_id)
        .options(selectinload(CandidateORM.skills).selectinload(CandidateSkillORM.skill))
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    return Candidate(
        id=row.id,
        full_name=row.full_name,
        email=row.email,
        summary=row.summary,
        skills=[
            CandidateSkill(
                skill=Skill(id=cs.skill.id, name=cs.skill.name, category=cs.skill.category),
                years_experience=cs.years_experience,
                proficiency=cs.proficiency,
            )
            for cs in row.skills
        ],
        total_years_experience=row.total_years_experience,
        target_role_type=row.target_role_type,
        raw_resume_text=row.raw_resume_text,
        created_at=row.created_at,
    )
