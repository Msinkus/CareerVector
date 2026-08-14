from careervector.domain.vacancies.models import Vacancy


def dedup_vacancies(vacancies: list[Vacancy]) -> list[Vacancy]:
    """Collapses postings that describe the same job, keeping the most recently posted one.

    Two vacancies are considered the same job if they share a company, title, role type,
    and seniority (case-insensitive on the free-text fields) — the same posting can appear
    more than once across ingestion runs or be cross-posted by the source.
    """
    latest_by_key: dict[tuple[str, str, str, str], Vacancy] = {}
    for vacancy in vacancies:
        key = (
            vacancy.company.strip().lower(),
            vacancy.title.strip().lower(),
            vacancy.role_type,
            vacancy.seniority,
        )
        existing = latest_by_key.get(key)
        if existing is None or vacancy.posted_at > existing.posted_at:
            latest_by_key[key] = vacancy
    return list(latest_by_key.values())
