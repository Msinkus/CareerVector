from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careervector.domain.skills.models import Skill
from careervector.infra.db.models import SkillORM


async def list_skills(session: AsyncSession) -> list[Skill]:
    result = await session.execute(select(SkillORM))
    return [
        Skill(id=row.id, name=row.name, category=row.category) for row in result.scalars().all()
    ]
