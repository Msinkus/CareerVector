import json
from pathlib import Path

import pytest

from careervector.ingestion.sources.base import VacancySource
from careervector.ingestion.sources.mock_source import MockVacancySource

pytestmark = pytest.mark.unit

_SAMPLE_RECORDS = [
    {
        "title": "Backend Engineer",
        "company": "Nimbus Systems",
        "role_type": "backend",
        "seniority": "mid",
        "description": "Build and operate backend services.",
        "skill_requirements": [
            {
                "skill": {"id": "python", "name": "Python", "category": "language"},
                "importance": "must_have",
                "min_years_experience": 2,
            }
        ],
        "location": "Remote",
        "remote": True,
        "source": "mock",
        "source_url": None,
        "posted_at": "2026-08-01T00:00:00Z",
    }
]


@pytest.fixture
def sample_data_path(tmp_path: Path) -> Path:
    path = tmp_path / "vacancies.json"
    path.write_text(json.dumps(_SAMPLE_RECORDS))
    return path


async def test_fetch_yields_validated_vacancies(sample_data_path: Path) -> None:
    source = MockVacancySource(data_path=sample_data_path)

    vacancies = [v async for v in source.fetch()]

    assert len(vacancies) == 1
    assert vacancies[0].title == "Backend Engineer"
    assert vacancies[0].skill_requirements[0].skill.id == "python"


async def test_mock_source_satisfies_vacancy_source_protocol(sample_data_path: Path) -> None:
    source = MockVacancySource(data_path=sample_data_path)

    assert isinstance(source, VacancySource)


async def test_fetch_default_path_reads_seeded_mock_data() -> None:
    source = MockVacancySource()

    vacancies = [v async for v in source.fetch()]

    assert len(vacancies) > 0
