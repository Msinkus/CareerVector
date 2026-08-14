from careervector.domain.matching.models import RetrievedItem
from careervector.infra.vector_store.qdrant_client import get_qdrant_client


class QdrantDenseRetriever:
    """Dense retrieval adapter implementing the domain `DenseRetriever` port."""

    def __init__(self, collection: str) -> None:
        self._collection = collection

    async def retrieve(self, query_embedding: list[float], top_k: int) -> list[RetrievedItem]:
        result = await get_qdrant_client().query_points(
            collection_name=self._collection, query=query_embedding, limit=top_k
        )
        return [RetrievedItem(id=str(point.id), score=point.score) for point in result.points]
