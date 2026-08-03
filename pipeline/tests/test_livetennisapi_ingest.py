from datetime import date

from pipeline.ingestion.livetennisapi_ingest import (
    build_tourney_id,
    clean_ioc,
    compute_score,
    extract_match,
)


def make_match(**overrides):
    """A completed match shaped like the provider's documented response."""
    match = {
        "id": 90001,
        "tournament": "Example Open",
        "surface": "hard",
        "indoor": False,
        "format": "BO3",
        "round": "QF",
        "status": "completed",
        "is_doubles": False,
        "scheduled_time": "2026-07-30T12:00:00Z",
        "players": {
            "p1": {
                "id": 1001,
                "name": "A Player",
                "country": "ESP",
                "ranking": 4,
                "ranking_points": 5100,
                "hand": "R",
            },
            "p2": {
                "id": 1002,
                "name": "B Player",
                "country": "USA",
                "ranking": 17,
                "ranking_points": 2260,
                "hand": "L",
            },
        },
        "score": {"sets": [2, 0], "games": [[6, 6], [4, 3]]},
        "winner": 1,
    }
    match.update(overrides)
    return match


def test_extract_match_orients_on_winner():
    row = extract_match(make_match())

    assert row["winner_name"] == "A Player"
    assert row["loser_name"] == "B Player"
    assert row["ltapi_winner_id"] == 1001
    assert row["ltapi_loser_id"] == 1002
    assert row["winner_rank"] == 4
    assert row["loser_rank"] == 17
    assert row["best_of"] == 3
    assert row["surface"] == "Hard"
    assert row["tourney_date"] == date(2026, 7, 30)


def test_extract_match_orients_when_player_two_wins():
    row = extract_match(make_match(winner=2))

    assert row["winner_name"] == "B Player"
    assert row["loser_name"] == "A Player"
    assert row["winner_rank"] == 17
    # score is reported p1 first, so it has to be flipped with the winner
    assert row["score"] == "4-6 3-6"


def test_extract_match_skips_matches_that_are_not_finished():
    assert extract_match(make_match(status="live")) == {}
    assert extract_match(make_match(status="upcoming")) == {}


def test_extract_match_skips_doubles_and_missing_winner():
    assert extract_match(make_match(is_doubles=True)) == {}
    assert extract_match(make_match(winner=None)) == {}


def test_extract_match_leaves_unavailable_fields_absent():
    row = extract_match(make_match())

    # the provider carries no serve/return stats, so these must stay NULL
    # rather than be zero filled
    for column in ["w_ace", "w_df", "w_svpt", "minutes", "draw_size", "tourney_level"]:
        assert column not in row


def test_extract_match_handles_null_surface_and_format():
    row = extract_match(make_match(surface=None, format=None))

    assert row["surface"] is None
    assert row["best_of"] is None


def test_compute_score_builds_a_set_by_set_string():
    assert compute_score({"games": [[6, 7], [4, 5]]}, 1) == "6-4 7-5"


def test_compute_score_returns_none_when_games_are_not_usable():
    # a completed match watched live can carry an empty games array
    assert compute_score({"games": []}, 1) is None
    assert compute_score({"games": [[6], []]}, 1) is None
    assert compute_score({"games": [[6, 7]]}, 1) is None
    assert compute_score({"games": [[6, None], [4, 5]]}, 1) is None
    assert compute_score({}, 1) is None
    assert compute_score(None, 1) is None


def test_clean_ioc_only_accepts_three_letter_codes():
    # the provider does not document the format of country, so anything that
    # is not clearly an IOC code is dropped instead of being written as one
    assert clean_ioc("ESP") == "ESP"
    assert clean_ioc("es") is None
    assert clean_ioc("Spain") is None
    assert clean_ioc(None) is None


def test_build_tourney_id_is_namespaced():
    assert build_tourney_id("Example Open") == "ltapi:example-open"
    assert build_tourney_id("Roland-Garros 2026") == "ltapi:roland-garros-2026"
    assert build_tourney_id(None) is None
