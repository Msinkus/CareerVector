from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from careervector.config import get_settings


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


async def ensure_collection(name: str, vector_size: int) -> None:
    client = get_qdrant_client()
    if not await client.collection_exists(name):
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


async def upsert_points(collection: str, points: list[PointStruct]) -> None:
    await get_qdrant_client().upsert(collection_name=collection, points=points)
