"""Generates realistic mock vacancies and seeds them into data/mock/vacancies.json and Postgres.

Run after `alembic upgrade head`:
    uv run python scripts/seed_mock_data.py
"""

import asyncio
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select

from careervector.domain.skills.models import Skill, SkillCategory, SkillImportance, SkillRequirement
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.infra.db.models import SkillORM, VacancyORM, VacancySkillRequirementORM
from careervector.infra.db.session import async_session_factory

SEED = 42
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mock" / "vacancies.json"

SKILLS: dict[str, Skill] = {
    s.id: s
    for s in [
        Skill(id="python", name="Python", category=SkillCategory.LANGUAGE),
        Skill(id="typescript", name="TypeScript", category=SkillCategory.LANGUAGE),
        Skill(id="java", name="Java", category=SkillCategory.LANGUAGE),
        Skill(id="go", name="Go", category=SkillCategory.LANGUAGE),
        Skill(id="sql", name="SQL", category=SkillCategory.LANGUAGE),
        Skill(id="fastapi", name="FastAPI", category=SkillCategory.FRAMEWORK),
        Skill(id="django", name="Django", category=SkillCategory.FRAMEWORK),
        Skill(id="spring", name="Spring", category=SkillCategory.FRAMEWORK),
        Skill(id="express", name="Express", category=SkillCategory.FRAMEWORK),
        Skill(id="pytorch", name="PyTorch", category=SkillCategory.FRAMEWORK),
        Skill(id="tensorflow", name="TensorFlow", category=SkillCategory.FRAMEWORK),
        Skill(id="langchain", name="LangChain", category=SkillCategory.FRAMEWORK),
        Skill(id="postgresql", name="PostgreSQL", category=SkillCategory.DATABASE),
        Skill(id="mysql", name="MySQL", category=SkillCategory.DATABASE),
        Skill(id="mongodb", name="MongoDB", category=SkillCategory.DATABASE),
        Skill(id="redis", name="Redis", category=SkillCategory.DATABASE),
        Skill(id="elasticsearch", name="Elasticsearch", category=SkillCategory.DATABASE),
        Skill(id="snowflake", name="Snowflake", category=SkillCategory.DATABASE),
        Skill(id="bigquery", name="BigQuery", category=SkillCategory.DATABASE),
        Skill(id="aws", name="AWS", category=SkillCategory.CLOUD),
        Skill(id="gcp", name="Google Cloud Platform", category=SkillCategory.CLOUD),
        Skill(id="azure", name="Azure", category=SkillCategory.CLOUD),
        Skill(id="docker", name="Docker", category=SkillCategory.CLOUD),
        Skill(id="kubernetes", name="Kubernetes", category=SkillCategory.CLOUD),
        Skill(id="terraform", name="Terraform", category=SkillCategory.CLOUD),
        Skill(id="git", name="Git", category=SkillCategory.TOOL),
        Skill(id="ci_cd", name="CI/CD", category=SkillCategory.TOOL),
        Skill(id="airflow", name="Airflow", category=SkillCategory.TOOL),
        Skill(id="kafka", name="Kafka", category=SkillCategory.TOOL),
        Skill(id="spark", name="Spark", category=SkillCategory.TOOL),
        Skill(id="dbt", name="dbt", category=SkillCategory.TOOL),
        Skill(id="prefect", name="Prefect", category=SkillCategory.TOOL),
        Skill(id="rest_apis", name="REST API Design", category=SkillCategory.CONCEPT),
        Skill(id="microservices", name="Microservices", category=SkillCategory.CONCEPT),
        Skill(id="system_design", name="System Design", category=SkillCategory.CONCEPT),
        Skill(id="distributed_systems", name="Distributed Systems", category=SkillCategory.CONCEPT),
        Skill(id="data_modeling", name="Data Modeling", category=SkillCategory.CONCEPT),
        Skill(id="data_pipelines", name="Data Pipeline Design", category=SkillCategory.CONCEPT),
        Skill(id="statistics", name="Statistics", category=SkillCategory.CONCEPT),
        Skill(id="machine_learning", name="Machine Learning", category=SkillCategory.CONCEPT),
        Skill(id="nlp", name="Natural Language Processing", category=SkillCategory.CONCEPT),
        Skill(id="llm_engineering", name="LLM Engineering", category=SkillCategory.CONCEPT),
        Skill(id="mlops", name="MLOps", category=SkillCategory.CONCEPT),
    ]
}

ROLE_SKILL_POOLS: dict[RoleType, dict[str, list[str]]] = {
    RoleType.BACKEND: {
        "must_have": [
            "python", "typescript", "java", "go", "fastapi", "django", "spring",
            "express", "postgresql", "mysql", "redis", "rest_apis", "microservices",
            "system_design", "distributed_systems",
        ],
        "nice_to_have": [
            "mongodb", "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
            "git", "ci_cd", "kafka",
        ],
    },
    RoleType.DATA: {
        "must_have": [
            "python", "sql", "postgresql", "snowflake", "bigquery", "airflow",
            "spark", "dbt", "data_modeling", "data_pipelines", "statistics",
        ],
        "nice_to_have": [
            "aws", "gcp", "azure", "kafka", "mongodb", "git", "distributed_systems", "prefect",
        ],
    },
    RoleType.AI_ENGINEERING: {
        "must_have": [
            "python", "pytorch", "tensorflow", "langchain", "machine_learning",
            "nlp", "llm_engineering", "statistics", "fastapi",
        ],
        "nice_to_have": [
            "aws", "gcp", "docker", "kubernetes", "redis", "elasticsearch",
            "mlops", "git", "ci_cd", "postgresql",
        ],
    },
}

TITLES: dict[RoleType, dict[SeniorityLevel, list[str]]] = {
    RoleType.BACKEND: {
        SeniorityLevel.JUNIOR: ["Junior Backend Engineer", "Associate Backend Developer"],
        SeniorityLevel.MID: ["Backend Engineer", "Backend Software Engineer"],
        SeniorityLevel.SENIOR: ["Senior Backend Engineer", "Senior Software Engineer, Backend"],
        SeniorityLevel.STAFF: ["Staff Backend Engineer", "Principal Backend Engineer"],
    },
    RoleType.DATA: {
        SeniorityLevel.JUNIOR: ["Junior Data Engineer", "Associate Data Engineer"],
        SeniorityLevel.MID: ["Data Engineer", "Data Platform Engineer"],
        SeniorityLevel.SENIOR: ["Senior Data Engineer", "Senior Data Platform Engineer"],
        SeniorityLevel.STAFF: ["Staff Data Engineer", "Principal Data Engineer"],
    },
    RoleType.AI_ENGINEERING: {
        SeniorityLevel.JUNIOR: ["Junior AI Engineer", "Associate Machine Learning Engineer"],
        SeniorityLevel.MID: ["AI Engineer", "Machine Learning Engineer"],
        SeniorityLevel.SENIOR: ["Senior AI Engineer", "Senior Machine Learning Engineer"],
        SeniorityLevel.STAFF: ["Staff AI Engineer", "Principal Machine Learning Engineer"],
    },
}

ROLE_LABELS: dict[RoleType, str] = {
    RoleType.BACKEND: "backend engineering",
    RoleType.DATA: "data engineering",
    RoleType.AI_ENGINEERING: "AI/ML engineering",
}

COMPANIES = [
    "Nimbus Systems", "Anchorage Labs", "Vertex Analytics", "Brightloop",
    "Cobalt Works", "Fernwood Technologies", "Lumen Data Co.", "Northstar AI",
    "Ridgeline Software", "Solace Cloud",
]

CITIES = ["Austin, TX", "New York, NY", "San Francisco, CA", "Seattle, WA", "Chicago, IL", "Denver, CO", "Boston, MA"]

MIN_YEARS_BY_SENIORITY: dict[SeniorityLevel, list[int]] = {
    SeniorityLevel.JUNIOR: [0, 1],
    SeniorityLevel.MID: [2, 3],
    SeniorityLevel.SENIOR: [4, 5, 6],
    SeniorityLevel.STAFF: [7, 8, 9],
}

REQUIREMENT_COUNTS: dict[SeniorityLevel, tuple[int, int]] = {
    SeniorityLevel.JUNIOR: (3, 2),
    SeniorityLevel.MID: (4, 2),
    SeniorityLevel.SENIOR: (5, 3),
    SeniorityLevel.STAFF: (6, 3),
}


def _build_description(
    role_type: RoleType, seniority: SeniorityLevel, company: str, must_ids: list[str], nice_ids: list[str]
) -> str:
    must_names = ", ".join(SKILLS[s].name for s in must_ids)
    nice_names = ", ".join(SKILLS[s].name for s in nice_ids)
    parts = [
        f"{company} is hiring a {seniority.value}-level {ROLE_LABELS[role_type]} professional to join our platform team.",
        "You will design, build, and operate production systems, working closely with cross-functional stakeholders.",
        f"Required: {must_names}.",
    ]
    if nice_names:
        parts.append(f"Nice to have: {nice_names}.")
    return " ".join(parts)


def generate_vacancies() -> list[Vacancy]:
    random.seed(SEED)
    now = datetime.now(UTC)
    vacancies: list[Vacancy] = []

    for role_type in RoleType:
        pool = ROLE_SKILL_POOLS[role_type]
        for seniority in SeniorityLevel:
            titles = TITLES[role_type][seniority]
            must_n, nice_n = REQUIREMENT_COUNTS[seniority]
            for company in random.sample(COMPANIES, k=3):
                must_ids = random.sample(pool["must_have"], k=min(must_n, len(pool["must_have"])))
                remaining_nice = [s for s in pool["nice_to_have"] if s not in must_ids]
                nice_ids = random.sample(remaining_nice, k=min(nice_n, len(remaining_nice)))
                min_years = random.choice(MIN_YEARS_BY_SENIORITY[seniority])

                skill_requirements = [
                    SkillRequirement(
                        skill=SKILLS[sid], importance=SkillImportance.MUST_HAVE, min_years_experience=min_years
                    )
                    for sid in must_ids
                ] + [
                    SkillRequirement(skill=SKILLS[sid], importance=SkillImportance.NICE_TO_HAVE)
                    for sid in nice_ids
                ]

                remote = random.random() < 0.4
                location = "Remote" if remote else random.choice(CITIES)
                posted_at = now - timedelta(days=random.randint(0, 45), hours=random.randint(0, 23))

                vacancy = Vacancy(
                    title=random.choice(titles),
                    company=company,
                    role_type=role_type,
                    seniority=seniority,
                    description=_build_description(role_type, seniority, company, must_ids, nice_ids),
                    skill_requirements=skill_requirements,
                    location=location,
                    remote=remote,
                    source="mock",
                    source_url=f"https://careervector.local/mock-postings/{len(vacancies) + 1}",
                    posted_at=posted_at,
                )
                vacancies.append(vacancy)

    return vacancies


def write_json(vacancies: list[Vacancy]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [json.loads(v.model_dump_json()) for v in vacancies]
    DATA_PATH.write_text(json.dumps(payload, indent=2) + "\n")


async def seed_database(vacancies: list[Vacancy]) -> None:
    async with async_session_factory() as session:
        existing_skill_ids = set((await session.execute(select(SkillORM.id))).scalars().all())
        for skill in SKILLS.values():
            if skill.id not in existing_skill_ids:
                session.add(SkillORM(id=skill.id, name=skill.name, category=skill.category))
        await session.flush()

        await session.execute(delete(VacancyORM))

        for vacancy in vacancies:
            session.add(
                VacancyORM(
                    id=vacancy.id,
                    title=vacancy.title,
                    company=vacancy.company,
                    role_type=vacancy.role_type,
                    seniority=vacancy.seniority,
                    description=vacancy.description,
                    location=vacancy.location,
                    remote=vacancy.remote,
                    source=vacancy.source,
                    source_url=vacancy.source_url,
                    posted_at=vacancy.posted_at,
                    ingested_at=vacancy.ingested_at,
                )
            )
            for req in vacancy.skill_requirements:
                session.add(
                    VacancySkillRequirementORM(
                        vacancy_id=vacancy.id,
                        skill_id=req.skill.id,
                        importance=req.importance,
                        min_years_experience=req.min_years_experience,
                    )
                )

        await session.commit()


async def main() -> None:
    vacancies = generate_vacancies()
    write_json(vacancies)
    print(f"Wrote {len(vacancies)} mock vacancies to {DATA_PATH}")

    await seed_database(vacancies)
    print(f"Seeded {len(vacancies)} vacancies and {len(SKILLS)} skills into Postgres")


if __name__ == "__main__":
    asyncio.run(main())
