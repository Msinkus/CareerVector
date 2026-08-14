import asyncio

from careervector.domain.matching.fusion import reciprocal_rank_fusion
from careervector.domain.matching.models import RetrievedItem
from careervector.domain.matching.ports import DenseRetriever, SparseRetriever


class HybridRetriever:
    """Fuses dense and sparse retrieval via Reciprocal Rank Fusion.

    Depends only on the DenseRetriever/SparseRetriever ports, so it carries no framework
    or infra imports — concrete adapters (Qdrant, BM25) live in infra/matching/. Reranking
    is a separate stage the caller runs afterward, since it needs to resolve fused ids to
    full entity text, which is a repository concern this class doesn't have access to.
    """

    def __init__(self, dense: DenseRetriever, sparse: SparseRetriever, rrf_k: int = 60) -> None:
        self._dense = dense
        self._sparse = sparse
        self._rrf_k = rrf_k

    async def retrieve(
        self, query_embedding: list[float], query_text: str, top_k: int
    ) -> list[RetrievedItem]:
        dense_results, sparse_results = await asyncio.gather(
            self._dense.retrieve(query_embedding, top_k),
            self._sparse.retrieve(query_text, top_k),
        )
        fused = reciprocal_rank_fusion([dense_results, sparse_results], k=self._rrf_k)
        return fused[:top_k]
