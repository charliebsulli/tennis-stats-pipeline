import logging

from sqlalchemy import text

from db.db_connection import engine

logger = logging.getLogger(__name__)


def compute_surface_stats():
    with engine.connect() as conn:
        # players who need their surface stats updated
        # 1. matches have been added for this player since their surface stats were last updated
        # or
        # 2. the player has no entries in surface stats but any complete entry in match_stats
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
        if len(players) == 0:
            logger.info("No players need surface stats updated.")
        else:
            logger.info("Updating surface stats")
            with open("pipeline/queries/player_stats_query.sql") as f:
                query = text(f.read())

            conn.execute(query, {"player_ids": players})
            conn.commit()
            logger.info(f"Updated surface stats for {len(players)} players")
