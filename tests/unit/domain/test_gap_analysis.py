from datetime import UTC, datetime

import pytest

from careervector.domain.candidates.models import Candidate, CandidateSkill
from careervector.domain.skills.gap_analysis import compute_skill_gap
from careervector.domain.skills.models import (
    Skill,
    SkillCategory,
    SkillImportance,
    SkillRequirement,
)
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy

pytestmark = pytest.mark.unit

_PYTHON = Skill(id="python", name="Python", category=SkillCategory.LANGUAGE)
_KUBERNETES = Skill(id="kubernetes", name="Kubernetes", category=SkillCategory.TOOL)
_KAFKA = Skill(id="kafka", name="Kafka", category=SkillCategory.TOOL)


def _make_vacancy(skill_requirements: list[SkillRequirement]) -> Vacancy:
    return Vacancy(
        title="Backend Engineer",
        company="Nimbus Systems",
        role_type=RoleType.BACKEND,
        seniority=SeniorityLevel.MID,
        description="Build things.",
        skill_requirements=skill_requirements,
        source="mock",
        posted_at=datetime.now(UTC),
    )


def _make_candidate(skills: list[CandidateSkill]) -> Candidate:
    return Candidate(full_name="Test Candidate", skills=skills)


def test_matched_skill_appears_in_matched_and_not_in_missing() -> None:
    vacancy = _make_vacancy(
        [SkillRequirement(skill=_PYTHON, importance=SkillImportance.MUST_HAVE)]
    )
    candidate = _make_candidate([CandidateSkill(skill=_PYTHON)])

    report = compute_skill_gap(candidate, vacancy)

    assert report.matched_skills == [_PYTHON]
    assert report.missing_must_have == []
    assert report.must_have_match_ratio == 1.0


def test_missing_must_have_skill_is_reported_separately_from_nice_to_have() -> None:
    vacancy = _make_vacancy(
        [
            SkillRequirement(skill=_PYTHON, importance=SkillImportance.MUST_HAVE),
            SkillRequirement(skill=_KUBERNETES, importance=SkillImportance.MUST_HAVE),
            SkillRequirement(skill=_KAFKA, importance=SkillImportance.NICE_TO_HAVE),
        ]
    )
    candidate = _make_candidate([CandidateSkill(skill=_PYTHON)])

    report = compute_skill_gap(candidate, vacancy)

    assert [req.skill.id for req in report.missing_must_have] == ["kubernetes"]
    assert [req.skill.id for req in report.missing_nice_to_have] == ["kafka"]
    assert report.must_have_match_ratio == pytest.approx(0.5)


def test_vacancy_with_no_must_haves_reports_full_match_ratio() -> None:
    vacancy = _make_vacancy(
        [SkillRequirement(skill=_KAFKA, importance=SkillImportance.NICE_TO_HAVE)]
    )
    candidate = _make_candidate([])

    report = compute_skill_gap(candidate, vacancy)

    assert report.must_have_match_ratio == 1.0
    assert [req.skill.id for req in report.missing_nice_to_have] == ["kafka"]
