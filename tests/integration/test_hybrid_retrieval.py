import pytest

from careervector.config import get_settings
from careervector.domain.matching.hybrid_retriever import HybridRetriever
from careervector.domain.matching.text import vacancy_match_text
from careervector.domain.vacancies.models import RoleType
from careervector.infra.db.repositories.vacancy_repository import list_vacancies
from careervector.infra.db.session import async_session_factory
from careervector.infra.embeddings.model import get_embedding_model
from careervector.infra.matching.dense_retriever import QdrantDenseRetriever
from careervector.infra.matching.reranker import get_reranker
from careervector.infra.matching.sparse_retriever import BM25VacancyRetriever

pytestmark = pytest.mark.integration

_AI_QUERY_TEXT = (
    "AI Engineer experienced in building LLM-powered agents with LangChain, PyTorch, "
    "and TensorFlow, deploying on AWS and Kubernetes."
)


async def test_hybrid_retrieval_ranks_ai_engineering_vacancies_highest_for_ai_query() -> None:
    async with async_session_factory() as session:
        vacancies = await list_vacancies(session)
    vacancy_by_id = {str(vacancy.id): vacancy for vacancy in vacancies}
    assert vacancy_by_id, "expected seeded vacancies — run scripts/seed_mock_data.py first"

    embedding_model = get_embedding_model()
    query_embedding = (await embedding_model.embed([_AI_QUERY_TEXT]))[0]

    hybrid = HybridRetriever(
        dense=QdrantDenseRetriever(get_settings().qdrant_collection_vacancies),
        sparse=BM25VacancyRetriever(
            [(str(vacancy.id), vacancy_match_text(vacancy)) for vacancy in vacancies]
        ),
    )
    fused = await hybrid.retrieve(query_embedding, _AI_QUERY_TEXT, top_k=10)

    top_role_types = [vacancy_by_id[item.id].role_type for item in fused[:5]]
    assert top_role_types.count(RoleType.AI_ENGINEERING) >= 3


async def test_cross_encoder_reranker_prefers_the_more_relevant_vacancy() -> None:
    async with async_session_factory() as session:
        vacancies = await list_vacancies(session)
    ai_vacancy = next(v for v in vacancies if v.role_type == RoleType.AI_ENGINEERING)
    backend_vacancy = next(v for v in vacancies if v.role_type == RoleType.BACKEND)

    reranker = get_reranker()
    reranked = await reranker.rerank(
        _AI_QUERY_TEXT,
        [
            (str(backend_vacancy.id), vacancy_match_text(backend_vacancy)),
            (str(ai_vacancy.id), vacancy_match_text(ai_vacancy)),
        ],
        top_k=2,
    )

    assert reranked[0].id == str(ai_vacancy.id)
