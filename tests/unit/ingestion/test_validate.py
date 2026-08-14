from datetime import UTC, datetime, timedelta

import pytest

from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.ingestion.pipelines.validate import VacancyValidationError, validate_vacancy

pytestmark = pytest.mark.unit

_PYTHON_REQUIREMENT = SkillRequirement(
    skill=Skill(id="python", name="Python", category=SkillCategory.LANGUAGE),
    importance=SkillImportance.MUST_HAVE,
)


def _make_vacancy(**overrides: object) -> Vacancy:
    defaults: dict[str, object] = {
        "title": "Backend Engineer",
        "company": "Nimbus Systems",
        "role_type": RoleType.BACKEND,
        "seniority": SeniorityLevel.MID,
        "description": "Build things.",
        "skill_requirements": [_PYTHON_REQUIREMENT],
        "source": "mock",
        "posted_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Vacancy(**defaults)  # type: ignore[arg-type]


def test_validate_accepts_well_formed_vacancy() -> None:
    validate_vacancy(_make_vacancy())


def test_validate_rejects_no_skill_requirements() -> None:
    vacancy = _make_vacancy(skill_requirements=[])

    with pytest.raises(VacancyValidationError):
        validate_vacancy(vacancy)


def test_validate_rejects_future_posted_at() -> None:
    vacancy = _make_vacancy(posted_at=datetime.now(UTC) + timedelta(days=1))

    with pytest.raises(VacancyValidationError):
        validate_vacancy(vacancy)
