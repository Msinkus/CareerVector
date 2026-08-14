import asyncio

from rank_bm25 import BM25Okapi

from careervector.domain.matching.models import RetrievedItem


class BM25VacancyRetriever:
    """In-memory BM25 sparse retrieval adapter implementing the domain `SparseRetriever` port.

    No dedicated search engine is in the stack (Elasticsearch/Solr are explicitly out of
    scope per CLAUDE.md), and the vacancy corpus is small enough to tokenize and score
    in-process per request rather than maintaining a persistent inverted index.
    """

    def __init__(self, corpus: list[tuple[str, str]]) -> None:
        self._ids = [item_id for item_id, _ in corpus]
        self._bm25 = BM25Okapi([text.lower().split() for _, text in corpus])

    async def retrieve(self, query_text: str, top_k: int) -> list[RetrievedItem]:
        scores = await asyncio.to_thread(self._bm25.get_scores, query_text.lower().split())
        ranked = sorted(
            zip(self._ids, scores, strict=True), key=lambda pair: pair[1], reverse=True
        )
        return [
            RetrievedItem(id=item_id, score=float(score))
            for item_id, score in ranked[:top_k]
            if score > 0
        ]
