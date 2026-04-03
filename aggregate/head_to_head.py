import logging

from sqlalchemy import text

from db.db_connection import engine

logger = logging.getLogger(__name__)


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
            logger.info("Updating head-to-head stats")
            with open("queries/h2h_query.sql") as f:
                query = text(f.read())

            conn.execute(query, {"player_ids": players})
            conn.commit()
            logger.info(f"Updated head-to-head stats for {len(players)} players")
