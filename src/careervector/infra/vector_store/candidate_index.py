from qdrant_client.models import PointStruct

from careervector.config import get_settings
from careervector.domain.candidates.models import Candidate
from careervector.infra.embeddings.model import EmbeddingModel
from careervector.infra.vector_store.qdrant_client import ensure_collection, upsert_points


def _embedding_text(candidate: Candidate) -> str:
    skill_names = ", ".join(cs.skill.name for cs in candidate.skills)
    summary = candidate.summary or ""
    return f"{candidate.full_name}. {summary} Skills: {skill_names}"


async def index_candidate(candidate: Candidate, model: EmbeddingModel) -> None:
    collection = get_settings().qdrant_collection_candidates
    await ensure_collection(collection, model.dimensions)

    embedding = (await model.embed([_embedding_text(candidate)]))[0]

    point = PointStruct(
        id=str(candidate.id),
        vector=embedding,
        payload={
            "candidate_id": str(candidate.id),
            "full_name": candidate.full_name,
            "target_role_type": candidate.target_role_type.value
            if candidate.target_role_type
            else None,
            "skill_ids": [cs.skill.id for cs in candidate.skills],
        },
    )
    await upsert_points(collection, [point])
