from datetime import date

import pandas as pd
from db_connection import engine
from sqlalchemy import create_engine, text

from player_id_helper import get_player_id

# set winner and loser id
def set_player_ids(row, conn):
    row["winner_id"] = get_player_id(row["rapidapi_winner_id"], row["winner_name"], conn)
    row["loser_id"] = get_player_id(row["rapidapi_loser_id"], row["loser_name"], conn)
    return row


# match api surface names to sackmann surface names
# everything else passes through
def map_surface_names(surface):
    surface_mapping = {
        "Hardcourt outdoor": "Hard",
        "Hardcourt indoor": "Hard",
        "Red clay": "Clay",
    }
    return surface_mapping.get(surface, surface)


def transform_raw_matches(sackmann_only: bool = False):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
                        SELECT * FROM raw_matches
                        WHERE match_id NOT IN (SELECT match_id FROM matches)
                        """), conn)
    if df.empty:
        print("No new matches found for transform.py")
        return

    if sackmann_only:
        df = df[df["source"] == "sackmann"]
    else:
        # processing for rapidapi data only
        
        # copy rapidapi_tournament_id to tourney_id
        mask = df["source"] == "rapidapi"
        df.loc[mask, "tourney_id"] = df.loc[mask, "rapidapi_tournament_id"].map(str)
        # set winner_id and loser_id to the translated player_ids
        with engine.connect() as conn:
            df.loc[mask, ["winner_id", "loser_id", "rapidapi_winner_id", "rapidapi_loser_id", "winner_name", "loser_name"]] = df.loc[mask, ["winner_id", "loser_id", "rapidapi_winner_id", "rapidapi_loser_id", "winner_name", "loser_name"]].apply(lambda row: set_player_ids(row, conn), axis=1)
        # normalize surface names
        df.loc[mask, "surface"] = df.loc[mask, "surface"].map(map_surface_names)
        # translate match_date from timestamp to date
        # so all dates are in the same format before processing
        df.loc[mask, "tourney_date"] = pd.to_datetime(df.loc[mask, "match_date"], unit='s') # .dt.strftime("%Y%m%d")

    # ===================================================================================
    # processing for all data, both sackmann and rapidapi

    # this handles some errors in sackmann data where the same player is on both sides of the match, 7 cases
    # will also protect against this happening in future data
    df = df[df["winner_id"] != df["loser_id"]]

    # tournaments
    dft = df.drop_duplicates("tourney_id")
    with engine.connect() as conn:
        tournament_ids = {row[0] for row in conn.execute(text("SELECT tournament_id FROM tournaments"))}
    new_tournaments = dft[~dft["tourney_id"].isin(tournament_ids)]
    new_tournaments = new_tournaments[["tourney_id", "tourney_name", "surface", "tourney_level"]]
    new_tournaments = new_tournaments.rename(columns={"tourney_id": "tournament_id", "tourney_name": "name", "tourney_level": "tournament_level"})
    new_tournaments = new_tournaments.fillna("Unknown") # name, surface, level
    
    # players
    with engine.connect() as conn:
        player_ids = {row[0] for row in conn.execute(text("SELECT player_id FROM players"))}

    df_winners = df.drop_duplicates("winner_id")
    new_winners = df_winners[~df_winners["winner_id"].isin(player_ids)]
    new_winners = new_winners[["winner_id", "winner_name", "winner_ioc", "winner_hand"]]
    new_winners = new_winners.rename(columns={"winner_id": "player_id", "winner_name": "name", "winner_ioc": "nationality", "winner_hand": "hand"})

    df_losers = df.drop_duplicates("loser_id")
    new_losers = df_losers[~df_losers["loser_id"].isin(player_ids)]
    new_losers = new_losers[["loser_id", "loser_name", "loser_ioc", "loser_hand"]]
    new_losers = new_losers.rename(columns={"loser_id": "player_id", "loser_name": "name", "loser_ioc": "nationality", "loser_hand": "hand"})

    new_players = pd.concat([new_winners, new_losers]).drop_duplicates("player_id")
    new_players["nationality"] = new_players["nationality"].fillna("Unknown")
    new_players["hand"] = new_players["hand"].fillna("U") # sackmann data uses U for unknown hand

    # matches
    new_matches = df[["match_id", "tourney_id", "round", "winner_id", "loser_id", "score"]]
    new_matches = new_matches.rename(columns={"tourney_id": "tournament_id"})
    new_matches["match_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d").dt.date
    new_matches["score"] = new_matches["score"].fillna("Unknown")

    # match_stats
    winner_stats = df[["match_id", "winner_id", "loser_id", "w_ace", "w_df", "w_svpt", "w_1stin", "w_1stwon", "w_2ndwon", "w_svgms", "w_bpsaved", "w_bpfaced"]].copy()
    winner_stats["won"] = True
    winner_stats["return_points"] = df["l_svpt"]
    winner_stats["first_serve_return_points"] = df["l_1stin"]
    winner_stats["first_serve_return_points_won"] = df["l_1stin"] - df["l_1stwon"]
    winner_stats["second_serve_return_points_won"] = df["l_svpt"] - df["l_1stin"] - df["l_2ndwon"]
    winner_stats["return_games"] = df["l_svgms"]
    winner_stats["break_points_converted"] = df["l_bpfaced"] - df["l_bpsaved"]
    winner_stats["break_points_chances"] = df["l_bpfaced"]
    winner_stats = winner_stats.rename(columns={"winner_id": "player_id", "loser_id": "opponent_id", "w_ace": "aces", "w_df": "double_faults", "w_svpt": "service_points", "w_1stin": "first_serves_in", "w_1stwon": "first_serve_points_won", "w_2ndwon": "second_serve_points_won", "w_svgms": "service_games", "w_bpsaved": "break_points_saved", "w_bpfaced": "break_points_faced"})

    loser_stats = df[["match_id", "loser_id", "winner_id", "l_ace", "l_df", "l_svpt", "l_1stin", "l_1stwon", "l_2ndwon", "l_svgms", "l_bpsaved", "l_bpfaced"]].copy()
    loser_stats["won"] = False
    loser_stats["return_points"] = df["w_svpt"]
    loser_stats["first_serve_return_points"] = df["w_1stin"]
    loser_stats["first_serve_return_points_won"] = df["w_1stin"] - df["w_1stwon"]
    loser_stats["second_serve_return_points_won"] = df["w_svpt"] - df["w_1stin"] - df["w_2ndwon"]
    loser_stats["return_games"] = df["w_svgms"]
    loser_stats["break_points_converted"] = df["w_bpfaced"] - df["w_bpsaved"]
    loser_stats["break_points_chances"] = df["w_bpfaced"]
    loser_stats = loser_stats.rename(columns={"loser_id": "player_id", "winner_id": "opponent_id", "l_ace": "aces", "l_df": "double_faults", "l_svpt": "service_points", "l_1stin": "first_serves_in", "l_1stwon": "first_serve_points_won", "l_2ndwon": "second_serve_points_won", "l_svgms": "service_games", "l_bpsaved": "break_points_saved", "l_bpfaced": "break_points_faced"})

    match_stats = pd.concat([winner_stats, loser_stats], ignore_index=True)
    match_stats_columns = ["aces", "double_faults", "service_points", "first_serves_in", "first_serve_points_won", "second_serve_points_won", "service_games", "break_points_saved", "break_points_faced", "return_points", "first_serve_return_points", "first_serve_return_points_won", "second_serve_return_points_won", "return_games", "break_points_converted", "break_points_chances"]
    match_stats["complete_stats"] = match_stats[match_stats_columns].notna().all(axis=1)

    # ===================================================================================

    with engine.begin() as conn:
        new_tournaments.to_sql("tournaments", conn, if_exists="append", index=False)
        new_players.to_sql("players", conn, if_exists="append", index=False)
        new_matches.to_sql("matches", conn, if_exists="append", index=False)
        match_stats.to_sql("match_stats", conn, if_exists="append", index=False)

if __name__ == "__main__":
    transform_raw_matches()