from uuid import uuid4

import pytest

from careervector.infra.db.repositories.vacancy_repository import (
    get_vacancy_by_id,
    list_vacancies,
)
from careervector.infra.db.session import async_session_factory

pytestmark = pytest.mark.integration


async def test_list_vacancies_returns_seeded_vacancies_with_skill_requirements() -> None:
    async with async_session_factory() as session:
        vacancies = await list_vacancies(session)

    assert len(vacancies) > 0
    assert any(vacancy.skill_requirements for vacancy in vacancies)


async def test_get_vacancy_by_id_round_trips_a_listed_vacancy() -> None:
    async with async_session_factory() as session:
        vacancies = await list_vacancies(session)
        target = vacancies[0]

        fetched = await get_vacancy_by_id(target.id, session)

    assert fetched is not None
    assert fetched.id == target.id
    assert fetched.title == target.title
    assert {req.skill.id for req in fetched.skill_requirements} == {
        req.skill.id for req in target.skill_requirements
    }


async def test_get_vacancy_by_id_returns_none_for_unknown_id() -> None:
    async with async_session_factory() as session:
        fetched = await get_vacancy_by_id(uuid4(), session)

    assert fetched is None
