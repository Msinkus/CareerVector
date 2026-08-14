from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from careervector.domain.vacancies.models import Vacancy
from careervector.infra.db.models import SkillORM, VacancyORM, VacancySkillRequirementORM


async def upsert_vacancies(vacancies: list[Vacancy], session: AsyncSession) -> None:
    """Upserts vacancies and any skills they reference, then commits.

    Skills are inserted if missing (the taxonomy only grows). Vacancies are upserted by
    id so repeated ingestion runs against a stable source converge rather than duplicate;
    each vacancy's skill requirements are replaced wholesale since there's no natural key
    finer than (vacancy_id, skill_id) worth diffing at this scale.
    """
    skills = {
        req.skill.id: req.skill for vacancy in vacancies for req in vacancy.skill_requirements
    }
    for skill in skills.values():
        stmt = pg_insert(SkillORM).values(id=skill.id, name=skill.name, category=skill.category)
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        await session.execute(stmt)

    for vacancy in vacancies:
        vacancy_values = {
            "title": vacancy.title,
            "company": vacancy.company,
            "role_type": vacancy.role_type,
            "seniority": vacancy.seniority,
            "description": vacancy.description,
            "location": vacancy.location,
            "remote": vacancy.remote,
            "source": vacancy.source,
            "source_url": vacancy.source_url,
            "posted_at": vacancy.posted_at,
            "ingested_at": vacancy.ingested_at,
        }
        stmt = pg_insert(VacancyORM).values(id=vacancy.id, **vacancy_values)
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=vacancy_values)
        await session.execute(stmt)

        await session.execute(
            delete(VacancySkillRequirementORM).where(
                VacancySkillRequirementORM.vacancy_id == vacancy.id
            )
        )
        for req in vacancy.skill_requirements:
            session.add(
                VacancySkillRequirementORM(
                    vacancy_id=vacancy.id,
                    skill_id=req.skill.id,
                    importance=req.importance,
                    min_years_experience=req.min_years_experience,
                )
            )

    await session.commit()
