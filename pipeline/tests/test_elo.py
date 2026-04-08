import pytest
from pipeline.aggregate.elo import expected_score


def test_expected_equal():
    assert expected_score(1500, 1500) == 0.5


def test_expected_sums_to_one():
    a = expected_score(1800, 1500)
    b = expected_score(1500, 1800)
    assert (a + b) == pytest.approx(1)


def test_expected_higher_elo():
    assert expected_score(1800, 1500) > 0.5
