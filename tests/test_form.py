from datetime import date, timedelta

import pandas as pd
import pytest

from aggregate.form import find_weighted_form


def test_weighted_form_all_wins():
    df = pd.DataFrame(
        [
            {"match_date": date.today() - timedelta(days=i), "won": True}
            for i in range(1, 6)
        ]
    )
    assert find_weighted_form(df, 0.97) == 1.0


def test_weighted_form_all_losses():
    df = pd.DataFrame(
        [
            {"match_date": date.today() - timedelta(days=i), "won": False}
            for i in range(1, 6)
        ]
    )
    assert find_weighted_form(df, 0.97) == 0.0


def test_weighted_form():
    df = pd.DataFrame(
        [
            {"match_date": date.today() - timedelta(days=i), "won": False}
            for i in range(1, 6)
        ]
        + [
            {"match_date": date.today() - timedelta(days=i), "won": True}
            for i in range(6, 10)
        ]
    )
    assert find_weighted_form(df, 0.97) == pytest.approx(0.4108245483)


def test_weighted_form_too_few_matches():
    df = pd.DataFrame()
    assert find_weighted_form(df, 0.97) is None
