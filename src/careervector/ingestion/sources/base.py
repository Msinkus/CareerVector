from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from careervector.domain.vacancies.models import Vacancy


@runtime_checkable
class VacancySource(Protocol):
    """Structural interface for anything that yields vacancy postings for ingestion.

    Downstream pipeline stages (dedup/clean/validate) treat everything yielded here as
    untrusted input, regardless of how well-formed a given implementation's data is.
    """

    def fetch(self) -> AsyncIterator[Vacancy]:
        """Yield vacancies from the source, one at a time."""
        ...
