import pytest

from careervector.infra.db.repositories.skill_repository import list_skills
from careervector.infra.db.session import async_session_factory

pytestmark = pytest.mark.integration


async def test_list_skills_returns_seeded_taxonomy() -> None:
    async with async_session_factory() as session:
        skills = await list_skills(session)

    assert len(skills) > 0
    assert any(skill.id == "python" for skill in skills)
