import logging
from collections import defaultdict

import pandas as pd
from sqlalchemy import text

from db_connection import engine

logger = logging.getLogger(__name__)


def get_current_ratings():
    with engine.connect() as conn:
        result = conn.execute(
            text("""SELECT DISTINCT ON (e.player_id, e.surface)
                        e.player_id,
                        e.surface,
                        e.elo_after
                    FROM elo_history AS e
                    JOIN matches AS m ON e.match_id = m.match_id
                    ORDER BY e.player_id, e.surface, e.match_date DESC, m.round_int DESC""")
        ).fetchall()

        ratings = defaultdict(
            lambda: 1500.0
        )  # TODO what if a player has other matches on other surfaces alr? those can inform rating start

        for row in result:
            ratings[(row.player_id, row.surface)] = row.elo_after

        return ratings


def get_matches_played_by_player_surface():
    """
    Returns a dictionary:
        {
            (player_id, surface): matches_count,
            (player_id, "ALL"): total_matches_count
        }
    representing the number of matches each player has played on each surface,
    and total matches across all surfaces. Counts both wins and losses.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    ms.player_id,
                    t.surface,
                    COUNT(*) AS matches_played
                FROM match_stats AS ms
                JOIN matches AS m ON ms.match_id = m.match_id
                JOIN tournaments AS t ON m.tournament_id = t.tournament_id
                GROUP BY ms.player_id, t.surface
            """)
        ).fetchall()

        matches_played = defaultdict(int)
        total_matches_per_player = defaultdict(int)

        for row in result:
            matches_played[(row.player_id, row.surface)] = row.matches_played
            total_matches_per_player[row.player_id] += row.matches_played

        # Add (player_id, "ALL") keys for each player
        for player_id, total in total_matches_per_player.items():
            matches_played[(player_id, "ALL")] = total

        return matches_played


# expected score for the first player's rating
def expected_score(rating_one, rating_two):
    e = 1 / (1 + 10 ** ((rating_two - rating_one) / 400))  # TODO read derivation
    return max(0.001, min(0.999, e))

def compute_k_factor(matches_played):
    """
    Compute the K-factor for ELO updates based on the number of matches played.
    Args:
        matches_played (int): Number of matches a player has played.

    Returns:
        int: K-factor (40 if matches played < 30, else 20)
    """
    if matches_played < 30:
        return 40
    else:
        return 20

def get_new_matches():
    with engine.connect() as conn:
        new_matches = pd.read_sql(
            text("""SELECT
                        m.match_id,
                        t.surface,
                        m.winner_id,
                        m.loser_id,
                        m.match_date
                    FROM matches AS m
                    JOIN tournaments AS t ON m.tournament_id = t.tournament_id
                    WHERE NOT EXISTS (
                        SELECT 1 FROM elo_history AS e WHERE e.match_id = m.match_id
                    )
                    ORDER BY m.match_date ASC, m.round_int ASC"""),
            conn,
        )

    return new_matches


def get_earliest_match_date():
    with engine.connect() as conn:
        result = conn.execute(
            text("""SELECT
                        MIN(m.match_date) AS earliest_new_date
                    FROM matches AS m
                    JOIN tournaments AS t ON m.tournament_id = t.tournament_id
                    WHERE NOT EXISTS (
                        SELECT 1 FROM elo_history AS e WHERE e.match_id = m.match_id
                    )""")
        ).fetchone()

    if not result:
        return None
    return result.earliest_new_date


def update_elo():
    earliest_match_date = get_earliest_match_date()

    if earliest_match_date is None:
        logger.info("No new matches to compute elo for")
        return

    # matches_played_by_player_surface = get_matches_played_by_player_surface()

    with engine.connect() as conn:
        # First, delete from averaged_surface_elo_history
        avg_result = conn.execute(
            text("""
            DELETE FROM averaged_surface_elo_history WHERE match_date >= :cutoff
            """),
            {"cutoff": earliest_match_date},
        )
        # Then, delete from elo_history
        result = conn.execute(
            text("""
            DELETE FROM elo_history WHERE match_date >= :cutoff
            """),
            {"cutoff": earliest_match_date},
        )
        conn.commit()

    if result.rowcount > 0:
        logger.warning(
            f"Recomputing elo for {result.rowcount} entries starting on {earliest_match_date}"
        )

    new_matches = get_new_matches()

    ratings = get_current_ratings()

    history = []
    averaged_surface_history = []
    for _, match in new_matches.iterrows():
        w_id = match["winner_id"]
        l_id = match["loser_id"]
        surface = match["surface"]

        # averaged ratings before the match, to compute expected score
        w_avg_surface_rating_before = (ratings[(w_id, surface)] + ratings[(w_id, "ALL")]) / 2
        l_avg_surface_rating_before = (ratings[(l_id, surface)] + ratings[(l_id, "ALL")]) / 2
        
        w_avg_expected_before = expected_score(w_avg_surface_rating_before, l_avg_surface_rating_before)
        l_avg_expected_before = 1 - w_avg_expected_before
        
        for s in [surface, "ALL"]:
            w_rating = ratings[(w_id, s)]
            l_rating = ratings[(l_id, s)]

            w_expected = expected_score(w_rating, l_rating)
            l_expected = 1 - w_expected

            # TODO can change k-factor depending on rating, num of recent matches, etc.
            # w_k = compute_k_factor(matches_played_by_player_surface[(w_id, s)])
            # l_k = compute_k_factor(matches_played_by_player_surface[(l_id, s)])

            w_k = 32
            l_k = 32

            w_new = w_rating + w_k * (1 - w_expected)
            l_new = l_rating + l_k * (0 - l_expected)


            # update in-memory ratings for subsequent matches
            ratings[(w_id, s)] = w_new
            ratings[(l_id, s)] = l_new

            history.extend(
                [
                    {
                        "player_id": w_id,
                        "match_id": match["match_id"],
                        "surface": s,
                        "match_date": match["match_date"],
                        "elo_before": w_rating,
                        "elo_after": w_new,
                        "k_factor": w_k,
                        "opponent_id": l_id,
                        "opponent_elo": l_rating,
                        "expected": w_expected,
                        "won": True,
                    },
                    {
                        "player_id": l_id,
                        "match_id": match["match_id"],
                        "surface": s,
                        "match_date": match["match_date"],
                        "elo_before": l_rating,
                        "elo_after": l_new,
                        "k_factor": l_k,
                        "opponent_id": w_id,
                        "opponent_elo": w_rating,
                        "expected": l_expected,
                        "won": False,
                    },
                ]
            )
        
        # averaged ratings after the match, to use for historical ranking
        w_avg_surface_rating_after = (ratings[(w_id, surface)] + ratings[(w_id, "ALL")]) / 2
        l_avg_surface_rating_after = (ratings[(l_id, surface)] + ratings[(l_id, "ALL")]) / 2
        
        averaged_surface_history.extend(
            [
                {
                    "player_id": w_id,
                    "match_id": match["match_id"],
                    "surface": surface,
                    "match_date": match["match_date"],
                    "expected": w_expected,
                    "won": True,
                    "averaged_surface_elo": w_avg_surface_rating_after,
                    "overall_surface": "ALL",
                },
                {
                    "player_id": l_id,
                    "match_id": match["match_id"],
                    "surface": surface,
                    "match_date": match["match_date"],
                    "expected": l_expected,
                    "won": False,
                    "averaged_surface_elo": l_avg_surface_rating_after,
                    "overall_surface": "ALL",
                },
            ]
        )
    with engine.begin() as conn:
        pd.DataFrame(history).to_sql(
            "elo_history", conn, if_exists="append", index=False
        )
        pd.DataFrame(averaged_surface_history).to_sql(
            "averaged_surface_elo_history", conn, if_exists="append", index=False
        )
    logger.info(f"Updated ELO for {len(new_matches)} matches")


# TODO injury break / other break k-factor logic
# TODO verify elo, check on clay court elo
