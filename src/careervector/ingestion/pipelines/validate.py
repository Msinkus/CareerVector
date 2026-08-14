from datetime import UTC, datetime

from careervector.domain.vacancies.models import Vacancy


class VacancyValidationError(ValueError):
    """Raised when a vacancy fails a business rule that Pydantic's type validation can't express."""


def validate_vacancy(vacancy: Vacancy) -> None:
    if not vacancy.title:
        raise VacancyValidationError("title must not be empty")
    if not vacancy.company:
        raise VacancyValidationError("company must not be empty")
    if not vacancy.skill_requirements:
        raise VacancyValidationError(
            f"vacancy '{vacancy.title}' at '{vacancy.company}' has no skill requirements"
        )
    if vacancy.posted_at > datetime.now(UTC):
        raise VacancyValidationError(f"vacancy '{vacancy.title}' has posted_at in the future")
