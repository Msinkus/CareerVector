import asyncio
from functools import lru_cache

from sentence_transformers import CrossEncoder

from careervector.config import get_settings
from careervector.domain.matching.models import RetrievedItem


class CrossEncoderReranker:
    """Reranking adapter implementing the domain `Reranker` port, wrapping a local
    sentence-transformers cross-encoder. Inference is CPU-bound and synchronous, so calls
    are offloaded to a thread, matching the convention in `infra/embeddings/model.py`.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model = CrossEncoder(model_name or get_settings().reranker_model_name)

    async def rerank(
        self, query_text: str, candidates: list[tuple[str, str]], top_k: int
    ) -> list[RetrievedItem]:
        if not candidates:
            return []
        pairs = [(query_text, text) for _, text in candidates]
        scores = await asyncio.to_thread(self._model.predict, pairs)
        ranked = sorted(
            zip((item_id for item_id, _ in candidates), scores, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [RetrievedItem(id=item_id, score=float(score)) for item_id, score in ranked[:top_k]]


@lru_cache
def get_reranker() -> CrossEncoderReranker:
    return CrossEncoderReranker()
