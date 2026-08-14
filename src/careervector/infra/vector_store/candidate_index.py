from qdrant_client.models import PointStruct

from careervector.config import get_settings
from careervector.domain.candidates.models import Candidate
from careervector.domain.matching.text import candidate_match_text
from careervector.infra.embeddings.model import EmbeddingModel
from careervector.infra.vector_store.qdrant_client import ensure_collection, upsert_points


async def index_candidate(candidate: Candidate, model: EmbeddingModel) -> None:
    collection = get_settings().qdrant_collection_candidates
    await ensure_collection(collection, model.dimensions)

    embedding = (await model.embed([candidate_match_text(candidate)]))[0]

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
