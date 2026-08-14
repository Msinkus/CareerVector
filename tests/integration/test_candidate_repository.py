from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.models import ProficiencyLevel
from careervector.infra.db.models import CandidateORM, CandidateSkillORM
from careervector.infra.db.repositories.candidate_repository import (
    create_candidate,
    get_candidate_by_id,
)
from careervector.infra.db.repositories.skill_repository import list_skills
from careervector.infra.db.session import async_session_factory

pytestmark = pytest.mark.integration


async def test_create_candidate_persists_candidate_and_skills() -> None:
    async with async_session_factory() as session:
        known_skills = await list_skills(session)
    python_skill = next(skill for skill in known_skills if skill.id == "python")

    candidate = Candidate(
        full_name="Integration Test Candidate",
        email="itest@example.com",
        skills=[
            CandidateSkill(
                skill=python_skill, years_experience=3, proficiency=ProficiencyLevel.ADVANCED
            )
        ],
    )

    try:
        async with async_session_factory() as session:
            await create_candidate(candidate, session)

        async with async_session_factory() as session:
            stored = (
                await session.execute(select(CandidateORM).where(CandidateORM.id == candidate.id))
            ).scalar_one()
            stored_skills = (
                (
                    await session.execute(
                        select(CandidateSkillORM).where(
                            CandidateSkillORM.candidate_id == candidate.id
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert stored.full_name == "Integration Test Candidate"
        assert len(stored_skills) == 1
        assert stored_skills[0].skill_id == "python"
    finally:
        async with async_session_factory() as session:
            await session.execute(delete(CandidateORM).where(CandidateORM.id == candidate.id))
            await session.commit()


async def test_get_candidate_by_id_round_trips_skills() -> None:
    async with async_session_factory() as session:
        known_skills = await list_skills(session)
    python_skill = next(skill for skill in known_skills if skill.id == "python")

    candidate = Candidate(
        full_name="Round Trip Candidate",
        skills=[
            CandidateSkill(
                skill=python_skill, years_experience=4, proficiency=ProficiencyLevel.ADVANCED
            )
        ],
    )

    try:
        async with async_session_factory() as session:
            await create_candidate(candidate, session)

        async with async_session_factory() as session:
            fetched = await get_candidate_by_id(candidate.id, session)

        assert fetched is not None
        assert fetched.full_name == "Round Trip Candidate"
        assert len(fetched.skills) == 1
        assert fetched.skills[0].skill.id == "python"
        assert fetched.skills[0].proficiency == ProficiencyLevel.ADVANCED
    finally:
        async with async_session_factory() as session:
            await session.execute(delete(CandidateORM).where(CandidateORM.id == candidate.id))
            await session.commit()


async def test_get_candidate_by_id_returns_none_for_unknown_id() -> None:
    async with async_session_factory() as session:
        fetched = await get_candidate_by_id(uuid4(), session)

    assert fetched is None
