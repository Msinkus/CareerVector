from qdrant_client.models import PointStruct

from careervector.config import get_settings
from careervector.domain.matching.text import vacancy_match_text
from careervector.domain.vacancies.models import Vacancy
from careervector.infra.embeddings.model import EmbeddingModel
from careervector.infra.vector_store.qdrant_client import ensure_collection, upsert_points


async def index_vacancies(vacancies: list[Vacancy], model: EmbeddingModel) -> None:
    if not vacancies:
        return

    collection = get_settings().qdrant_collection_vacancies
    await ensure_collection(collection, model.dimensions)

    texts = [vacancy_match_text(vacancy) for vacancy in vacancies]
    embeddings = await model.embed(texts)

    points = [
        PointStruct(
            id=str(vacancy.id),
            vector=embedding,
            payload={
                "vacancy_id": str(vacancy.id),
                "title": vacancy.title,
                "company": vacancy.company,
                "role_type": vacancy.role_type.value,
                "seniority": vacancy.seniority.value,
                "skill_ids": [req.skill.id for req in vacancy.skill_requirements],
            },
        )
        for vacancy, embedding in zip(vacancies, embeddings, strict=True)
    ]
    await upsert_points(collection, points)
