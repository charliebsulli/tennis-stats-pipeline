from sqlalchemy import text

from db_connection import engine

def compute_player_surface_stats():
    with engine.connect() as conn:
        # get the players who need their surface stats updated
        # either 1. matches have been added for this player since their surface stats were last updated
        # or 2. the player has no entries in surface stats but any complete entry in match_stats
        # many old players (pre 1991) have no match stats so I want to exclude them
        players = conn.execute(text("SELECT p.player_id FROM players AS p "
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
                            ")")).fetchall()
        players = [row[0] for row in players]
        # also need players who do NOT appear in the surface stats table\
        if len(players) == 0:
            print("No players need surface stats updated.")
        else:
            # update their surface stats
            with open("player_stats_query.sql") as f:
                query = text(f.read())

            conn.execute(query, {"player_ids": players})
            conn.commit()

if __name__ == "__main__":
    compute_player_surface_stats()