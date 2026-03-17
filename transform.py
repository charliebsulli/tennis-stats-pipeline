from datetime import date

import pandas as pd
from db_connection import get_connection

if __name__ == "__main__":
    conn = get_connection()
    curr = conn.cursor()

    df = pd.read_sql("""
                     SELECT * FROM raw_matches
                     WHERE match_id NOT IN (SELECT match_id FROM matches)
                     """, conn)

    # tournaments
    dft = df.drop_duplicates("tourney_id")
    tournament_ids = {row[0] for row in curr.execute("SELECT tournament_id FROM tournaments")}
    new_tournaments = dft[~dft["tourney_id"].isin(tournament_ids)]
    new_tournaments = new_tournaments[["tourney_id", "tourney_name", "surface", "tourney_level"]]
    new_tournaments = new_tournaments.rename(columns={"tourney_id": "tournament_id", "tourney_name": "name", "tourney_level": "tournament_level"})
    new_tournaments = new_tournaments.fillna("Unknown")
    
    new_tournaments.to_sql("tournaments", conn, if_exists="append", index=False)

    # players
    player_ids = {row[0] for row in curr.execute("SELECT player_id FROM players")}

    df_winners = df.drop_duplicates("winner_id")
    new_winners = df_winners[~df_winners["winner_id"].isin(player_ids)]
    new_winners = new_winners[["winner_id", "winner_name", "winner_ioc", "winner_hand"]]
    new_winners = new_winners.rename(columns={"winner_id": "player_id", "winner_name": "name", "winner_ioc": "nationality", "winner_hand": "hand"})

    df_losers = df.drop_duplicates("loser_id")
    new_losers = df_losers[~df_losers["loser_id"].isin(player_ids)]
    new_losers = new_losers[["loser_id", "loser_name", "loser_ioc", "loser_hand"]]
    new_losers = new_losers.rename(columns={"loser_id": "player_id", "loser_name": "name", "loser_ioc": "nationality", "loser_hand": "hand"})

    new_players = pd.concat([new_winners, new_losers]).drop_duplicates("player_id")
    new_players["dob"] = "Unknown"
    new_players = new_players.fillna("Unknown")

    new_players.to_sql("players", conn, if_exists="append", index=False)

    # matches
    new_matches = df[["match_id", "tourney_id", "round", "winner_id", "loser_id", "score"]]
    new_matches = new_matches.rename(columns={"tourney_id": "tournament_id"})
    new_matches["match_date"] = date.today() # TODO

    new_matches.to_sql("matches", conn, if_exists="append", index=False)
