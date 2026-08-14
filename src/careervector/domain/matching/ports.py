from typing import Protocol

from careervector.domain.matching.models import RetrievedItem


class DenseRetriever(Protocol):
    """Vector similarity search over an embedding index (e.g. Qdrant)."""

    async def retrieve(self, query_embedding: list[float], top_k: int) -> list[RetrievedItem]: ...


class SparseRetriever(Protocol):
    """Lexical search over a text corpus (e.g. BM25)."""

    async def retrieve(self, query_text: str, top_k: int) -> list[RetrievedItem]: ...


class Reranker(Protocol):
    """Pointwise reranking of a candidate set against a query, e.g. via a cross-encoder.

    `candidates` is a list of (id, text) pairs — the caller is responsible for resolving
    ids to text, since only it knows where the underlying entities live.
    """

    async def rerank(
        self, query_text: str, candidates: list[tuple[str, str]], top_k: int
    ) -> list[RetrievedItem]: ...
