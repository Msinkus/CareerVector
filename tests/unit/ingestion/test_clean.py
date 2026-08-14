from datetime import UTC, datetime

import pytest

from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.ingestion.pipelines.clean import clean_vacancy

pytestmark = pytest.mark.unit


def test_clean_vacancy_normalizes_whitespace() -> None:
    vacancy = Vacancy(
        title="  Backend   Engineer\n",
        company="Nimbus\tSystems",
        role_type=RoleType.BACKEND,
        seniority=SeniorityLevel.MID,
        description="Build   things.\n\nOperate   them.",
        skill_requirements=[
            SkillRequirement(
                skill=Skill(id="python", name="Python", category=SkillCategory.LANGUAGE),
                importance=SkillImportance.MUST_HAVE,
            )
        ],
        location="  Remote  ",
        source="mock",
        posted_at=datetime.now(UTC),
    )

    cleaned = clean_vacancy(vacancy)

    assert cleaned.title == "Backend Engineer"
    assert cleaned.company == "Nimbus Systems"
    assert cleaned.description == "Build things. Operate them."
    assert cleaned.location == "Remote"


def test_clean_vacancy_leaves_none_location_untouched() -> None:
    vacancy = Vacancy(
        title="Backend Engineer",
        company="Nimbus Systems",
        role_type=RoleType.BACKEND,
        seniority=SeniorityLevel.MID,
        description="Build things.",
        skill_requirements=[
            SkillRequirement(
                skill=Skill(id="python", name="Python", category=SkillCategory.LANGUAGE),
                importance=SkillImportance.MUST_HAVE,
            )
        ],
        location=None,
        source="mock",
        posted_at=datetime.now(UTC),
    )

    cleaned = clean_vacancy(vacancy)

    assert cleaned.location is None
