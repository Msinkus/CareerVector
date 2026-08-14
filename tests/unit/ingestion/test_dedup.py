from datetime import UTC, datetime, timedelta

import pytest

from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.ingestion.pipelines.dedup import dedup_vacancies

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


def test_dedup_collapses_same_job_keeping_most_recent() -> None:
    older = _make_vacancy(posted_at=datetime.now(UTC) - timedelta(days=5))
    newer = _make_vacancy(posted_at=datetime.now(UTC))

    result = dedup_vacancies([older, newer])

    assert result == [newer]


def test_dedup_is_case_and_whitespace_insensitive_on_key_fields() -> None:
    first = _make_vacancy(title="Backend Engineer", company="Nimbus Systems")
    duplicate = _make_vacancy(title="  backend engineer  ", company="NIMBUS SYSTEMS")

    result = dedup_vacancies([first, duplicate])

    assert len(result) == 1


def test_dedup_keeps_distinct_jobs() -> None:
    backend = _make_vacancy(title="Backend Engineer", company="Nimbus Systems")
    data = _make_vacancy(title="Data Engineer", company="Nimbus Systems", role_type=RoleType.DATA)

    result = dedup_vacancies([backend, data])

    assert len(result) == 2
