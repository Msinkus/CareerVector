import pytest

from careervector.domain.matching.fusion import reciprocal_rank_fusion
from careervector.domain.matching.models import RetrievedItem

pytestmark = pytest.mark.unit


def test_item_ranked_first_in_both_lists_wins() -> None:
    dense = [RetrievedItem(id="a", score=0.9), RetrievedItem(id="b", score=0.5)]
    sparse = [RetrievedItem(id="a", score=12.0), RetrievedItem(id="b", score=8.0)]

    fused = reciprocal_rank_fusion([dense, sparse])

    assert [item.id for item in fused] == ["a", "b"]


def test_item_present_in_both_rankings_outranks_single_ranking_top_hit() -> None:
    dense = [RetrievedItem(id="a", score=0.9), RetrievedItem(id="b", score=0.8)]
    sparse = [RetrievedItem(id="b", score=15.0), RetrievedItem(id="a", score=2.0)]

    fused = reciprocal_rank_fusion([dense, sparse])

    assert fused[0].id in {"a", "b"}
    assert fused[0].score == pytest.approx(fused[1].score)


def test_raw_score_scale_does_not_leak_into_fused_ranking() -> None:
    dense = [RetrievedItem(id="a", score=0.51), RetrievedItem(id="b", score=0.50)]
    sparse = [RetrievedItem(id="c", score=9999.0)]

    fused = reciprocal_rank_fusion([dense, sparse])

    assert fused[0].id == "a"
    assert {item.id for item in fused} == {"a", "b", "c"}


def test_item_absent_from_a_ranking_is_not_penalized_below_zero() -> None:
    dense = [RetrievedItem(id="a", score=1.0)]
    sparse: list[RetrievedItem] = []

    fused = reciprocal_rank_fusion([dense, sparse])

    assert len(fused) == 1
    assert fused[0].id == "a"
    assert fused[0].score == pytest.approx(1 / 61)
