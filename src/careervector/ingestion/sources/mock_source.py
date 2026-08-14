import json
from collections.abc import AsyncIterator
from pathlib import Path

from careervector.domain.vacancies.models import Vacancy

_DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "data" / "mock" / "vacancies.json"


class MockVacancySource:
    """Reads pre-generated mock vacancy postings from data/mock/vacancies.json.

    Stands in for a real external job board/API source during local development and
    demos, per the project's mock/pluggable ingestion architecture (live scraping is
    explicitly out of scope).
    """

    def __init__(self, data_path: Path = _DEFAULT_DATA_PATH) -> None:
        self._data_path = data_path

    async def fetch(self) -> AsyncIterator[Vacancy]:
        records = json.loads(self._data_path.read_text())
        for record in records:
            yield Vacancy.model_validate(record)
