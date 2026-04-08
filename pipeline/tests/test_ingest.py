from pipeline.ingestion.ingest import compute_score


def test_compute_score_three_sets():
    winner_score = {"period1": 6, "period2": 2, "period3": 6}
    loser_score = {"period1": 3, "period2": 6, "period3": 4}
    assert compute_score(winner_score, loser_score) == "6-3 2-6 6-4"


def test_compute_score_four_sets():
    winner_score = {"period1": 6, "period2": 2, "period3": 6, "period4": 6}
    loser_score = {"period1": 3, "period2": 6, "period3": 4, "period4": 0}
    assert compute_score(winner_score, loser_score) == "6-3 2-6 6-4 6-0"
