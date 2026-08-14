from pydantic import BaseModel


class RetrievedItem(BaseModel):
    """A single scored result from a retrieval or reranking stage, keyed by entity id."""

    id: str
    score: float
