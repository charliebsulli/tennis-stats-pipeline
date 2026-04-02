import logging
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import text

from db_connection import engine
from elo import update_elo

logger = logging.getLogger(__name__)


def compute_surface_stats():  # TODO these two queries are very similar
    with engine.connect() as conn:
        # get the players who need their surface stats updated
        # either 1. matches have been added for this player since their surface stats were last updated
        # or 2. the player has no entries in surface stats but any complete entry in match_stats
        # many old players (pre 1991) have no match stats so I want to exclude them
        players = conn.execute(
            text(
                "SELECT p.player_id FROM players AS p "
                "JOIN player_surface_stats AS ps ON p.player_id = ps.player_id "
                "JOIN match_stats AS ms on p.player_id = ms.player_id "
                "JOIN raw_matches AS r on ms.match_id = r.match_id "
                "WHERE ps.surface = 'ALL' AND ps.season = 0 "
                "GROUP BY p.player_id "
                "HAVING MAX(r.time_added) > MIN(ps.last_updated) "
                "UNION ALL "
                "SELECT p.player_id FROM players AS p "
                "WHERE NOT EXISTS ( "
                "SELECT 1 FROM player_surface_stats AS ps WHERE ps.player_id = p.player_id "
                ") AND EXISTS ("
                "SELECT 1 FROM match_stats AS ms WHERE ms.player_id = p.player_id AND ms.complete_stats "
                ")"
            )
        ).fetchall()
        players = [row[0] for row in players]
        # also need players who do NOT appear in the surface stats table\
        if len(players) == 0:
            logger.info("No players need surface stats updated.")
        else:
            # update their surface stats
            with open("queries/player_stats_query.sql") as f:
                query = text(f.read())

            conn.execute(query, {"player_ids": players})
            conn.commit()
            logger.info(f"Updated surface stats for {len(players)} players")


def compute_head_to_head():
    with engine.connect() as conn:
        players = conn.execute(
            text(
                "SELECT p.player_id FROM players AS p "
                "JOIN head_to_head AS h ON p.player_id = h.player_id "
                "JOIN match_stats AS ms on p.player_id = ms.player_id "
                "JOIN raw_matches AS r on ms.match_id = r.match_id "
                "WHERE h.surface = 'ALL' "
                "GROUP BY p.player_id "
                "HAVING MAX(r.time_added) > MIN(h.last_updated) "
                "UNION ALL "
                "SELECT p.player_id FROM players AS p "
                "WHERE NOT EXISTS ( "
                "SELECT 1 FROM head_to_head AS h WHERE h.player_id = p.player_id "
                ") AND EXISTS ("
                "SELECT 1 FROM match_stats AS ms WHERE ms.player_id = p.player_id "
                ")"
            )
        ).fetchall()
        players = [row[0] for row in players]
        if len(players) == 0:
            logger.info("No players need head to head records updated.")
        else:
            with open("queries/h2h_query.sql") as f:
                query = text(f.read())

            conn.execute(query, {"player_ids": players})
            conn.commit()
            logger.info(f"Updated head-to-head stats for {len(players)} players")


# TODO can calibrate weighting fn, how far back we look for matches
def compute_form():
    with engine.connect() as conn:
        with open("queries/recent_matches.sql") as f:
            query = text(f.read())
        df = pd.read_sql(query, conn)

    grouped = df.groupby(["player_id", "surface"])
    output = []
    for (player_id, surface), group in grouped:
        output.append(
            {
                "matches_total": len(group),
                "won": sum(group["won"]),
                "player_id": player_id,
                "surface": surface,
                "last_updated": datetime.now(timezone.utc),
                "weighted_form": find_weighted_form(group, 0.97),
            }
        )
    result = pd.DataFrame(output)
    with engine.begin() as conn:
        result.to_sql("player_form", conn, if_exists="delete_rows", index=False)
    logger.info("Updated player form")


def find_weighted_form(df: pd.DataFrame, alpha: float):
    if len(df) < 5:
        logger.info(
            f"Skipping player form for player with {len(df)} matches in last 90 days"
        )
        return None
    score, total = 0, 0
    now = date.today()
    for index, row in df.iterrows():
        days_ago = (now - row["match_date"]).days
        weight = alpha**days_ago
        total += weight
        if row["won"]:
            score += weight
    if total == 0:
        logger.warning("Total score for form computation is 0")
        return None
    return score / total


def derive_stats():
    compute_player_surface_stats()
    compute_head_to_head()
    compute_form()
    update_elo()
