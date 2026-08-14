from careervector.domain.matching.models import RetrievedItem


def reciprocal_rank_fusion(
    rankings: list[list[RetrievedItem]], k: int = 60
) -> list[RetrievedItem]:
    """Combines multiple ranked lists into one via Reciprocal Rank Fusion.

    Each id is scored by summing 1/(k + rank) across every ranking it appears in. RRF is
    used specifically because it's insensitive to each retriever's raw score scale — it
    fuses dense cosine similarity with BM25 scores cleanly without either needing
    normalization first.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item.id] = scores.get(item.id, 0.0) + 1.0 / (k + rank)
    return [
        RetrievedItem(id=item_id, score=score)
        for item_id, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    ]
