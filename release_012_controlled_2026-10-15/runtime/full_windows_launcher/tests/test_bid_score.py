from tenderproof.services.bid_score_service import calculate_score, recommendation_for_percentage


class Row:
    def __init__(self, score, max_score=5):
        self.score = score
        self.max_score = max_score


def test_total_score_calculation_works():
    total, max_score, pct = calculate_score([Row(4), Row(5), Row(1)])
    assert total == 10
    assert max_score == 15
    assert round(pct, 2) == 66.67


def test_recommendation_thresholds_work():
    assert recommendation_for_percentage(85) == "Pursue"
    assert recommendation_for_percentage(70) == "Pursue with partner"
    assert recommendation_for_percentage(55) == "Pursue only as sub-consultant"
    assert recommendation_for_percentage(40) == "Reject / No-bid"
    assert recommendation_for_percentage(90, missing_inputs=True) == "Pending input"

