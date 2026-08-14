"""Prefect flow: ingest -> dedup -> clean -> validate -> persist.

Run directly for local development:
    uv run python -m careervector.ingestion.flows.vacancy_ingestion
"""

import asyncio

from prefect import flow, task

from careervector.domain.vacancies.models import Vacancy
from careervector.infra.db.repositories.vacancy_repository import upsert_vacancies
from careervector.infra.db.session import async_session_factory
from careervector.ingestion.pipelines.clean import clean_vacancy
from careervector.ingestion.pipelines.dedup import dedup_vacancies
from careervector.ingestion.pipelines.validate import VacancyValidationError, validate_vacancy
from careervector.ingestion.sources.base import VacancySource
from careervector.ingestion.sources.mock_source import MockVacancySource


@task
async def ingest(source: VacancySource) -> list[Vacancy]:
    return [vacancy async for vacancy in source.fetch()]


@task
def dedup(vacancies: list[Vacancy]) -> list[Vacancy]:
    return dedup_vacancies(vacancies)


@task
def clean(vacancies: list[Vacancy]) -> list[Vacancy]:
    return [clean_vacancy(vacancy) for vacancy in vacancies]


@task
def validate(vacancies: list[Vacancy]) -> list[Vacancy]:
    valid: list[Vacancy] = []
    for vacancy in vacancies:
        try:
            validate_vacancy(vacancy)
        except VacancyValidationError:
            continue
        valid.append(vacancy)
    return valid


@task
async def persist(vacancies: list[Vacancy]) -> None:
    async with async_session_factory() as session:
        await upsert_vacancies(vacancies, session)


@flow(name="vacancy-ingestion")
async def vacancy_ingestion_flow(source: VacancySource | None = None) -> int:
    source = source or MockVacancySource()
    raw = await ingest(source)
    deduped = dedup(raw)
    cleaned = clean(deduped)
    valid = validate(cleaned)
    await persist(valid)
    return len(valid)


if __name__ == "__main__":
    count = asyncio.run(vacancy_ingestion_flow())
    print(f"Ingested {count} vacancies")
