import pytest

from careervector.domain.matching.hybrid_retriever import HybridRetriever
from careervector.domain.matching.models import RetrievedItem

pytestmark = pytest.mark.unit


class _FakeDenseRetriever:
    def __init__(self, results: list[RetrievedItem]) -> None:
        self._results = results

    async def retrieve(self, query_embedding: list[float], top_k: int) -> list[RetrievedItem]:
        return self._results[:top_k]


class _FakeSparseRetriever:
    def __init__(self, results: list[RetrievedItem]) -> None:
        self._results = results

    async def retrieve(self, query_text: str, top_k: int) -> list[RetrievedItem]:
        return self._results[:top_k]


async def test_hybrid_retriever_fuses_and_truncates_to_top_k() -> None:
    dense = _FakeDenseRetriever(
        [RetrievedItem(id="v1", score=0.9), RetrievedItem(id="v2", score=0.8)]
    )
    sparse = _FakeSparseRetriever(
        [RetrievedItem(id="v2", score=10.0), RetrievedItem(id="v3", score=5.0)]
    )
    retriever = HybridRetriever(dense=dense, sparse=sparse)

    fused = await retriever.retrieve(
        query_embedding=[0.1, 0.2], query_text="python backend", top_k=2
    )

    assert len(fused) == 2
    assert fused[0].id == "v2"


async def test_hybrid_retriever_calls_dense_and_sparse_with_retrieve_top_k() -> None:
    calls: dict[str, int] = {}

    class _RecordingDense(_FakeDenseRetriever):
        async def retrieve(self, query_embedding: list[float], top_k: int) -> list[RetrievedItem]:
            calls["dense_top_k"] = top_k
            return await super().retrieve(query_embedding, top_k)

    class _RecordingSparse(_FakeSparseRetriever):
        async def retrieve(self, query_text: str, top_k: int) -> list[RetrievedItem]:
            calls["sparse_top_k"] = top_k
            return await super().retrieve(query_text, top_k)

    retriever = HybridRetriever(dense=_RecordingDense([]), sparse=_RecordingSparse([]))

    await retriever.retrieve(query_embedding=[0.1], query_text="q", top_k=25)

    assert calls == {"dense_top_k": 25, "sparse_top_k": 25}
