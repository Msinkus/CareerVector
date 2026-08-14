import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from careervector.config import get_settings


class EmbeddingModel:
    """Wraps a local sentence-transformers model for dense embedding generation.

    Inference is CPU-bound and sentence-transformers has no async API, so calls are
    offloaded to a thread to avoid blocking the event loop.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model = SentenceTransformer(model_name or get_settings().embedding_model_name)

    @property
    def dimensions(self) -> int:
        return int(self._model.get_embedding_dimension())

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = await asyncio.to_thread(self._model.encode, texts, normalize_embeddings=True)
        return [row.tolist() for row in embeddings]


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
