from careervector.domain.candidates.models import Candidate
from careervector.domain.vacancies.models import Vacancy


def vacancy_match_text(vacancy: Vacancy) -> str:
    skill_names = ", ".join(req.skill.name for req in vacancy.skill_requirements)
    return f"{vacancy.title} at {vacancy.company}. {vacancy.description} Skills: {skill_names}"


def candidate_match_text(candidate: Candidate) -> str:
    skill_names = ", ".join(cs.skill.name for cs in candidate.skills)
    summary = candidate.summary or ""
    return f"{candidate.full_name}. {summary} Skills: {skill_names}"
