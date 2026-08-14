import re

from careervector.domain.vacancies.models import Vacancy

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def clean_vacancy(vacancy: Vacancy) -> Vacancy:
    """Normalizes whitespace in free-text fields (collapsing runs, trimming ends).

    Real-world sources routinely produce inconsistent whitespace (HTML-stripped
    descriptions, copy-pasted titles); the mock source is already clean, but this stage
    exists so a future non-mock source doesn't need its own cleaning logic.
    """
    return vacancy.model_copy(
        update={
            "title": _normalize(vacancy.title),
            "company": _normalize(vacancy.company),
            "description": _normalize(vacancy.description),
            "location": _normalize(vacancy.location) if vacancy.location else vacancy.location,
        }
    )
