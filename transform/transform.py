import logging

import pandas as pd
from rapidfuzz import fuzz, process
from sqlalchemy import text

from constants import ROUND_ORDER
from db.db_connection import engine
from transform.player_id_helper import (
    get_normalized_player_name_dict,
    get_player_id,
    get_player_id_lookup_dict,
    normalize_name,
)

logger = logging.getLogger(__name__)


# set winner and loser id
def set_player_ids(row, conn):
    row["winner_id"] = get_player_id(
        row["rapidapi_winner_id"], row["winner_name"], conn
    )
    row["loser_id"] = get_player_id(row["rapidapi_loser_id"], row["loser_name"], conn)
    return row


# match api surface names to sackmann surface names
# everything else passes through
# TODO put in constants file
def map_surface_names(surface):
    surface_mapping = {
        "Hardcourt outdoor": "Hard",
        "Hardcourt indoor": "Hard",
        "Red clay": "Clay",
    }
    return surface_mapping.get(surface, surface)


def transform_tournaments(df):
    dft = df.drop_duplicates("tourney_id")
    with engine.connect() as conn:
        tournament_ids = {
            row[0]
            for row in conn.execute(text("SELECT tournament_id FROM tournaments"))
        }
    new_tournaments = dft[~dft["tourney_id"].isin(tournament_ids)]
    new_tournaments = new_tournaments[
        ["tourney_id", "tourney_name", "surface", "tourney_level"]
    ]
    new_tournaments = new_tournaments.rename(
        columns={
            "tourney_id": "tournament_id",
            "tourney_name": "name",
            "tourney_level": "tournament_level",
        }
    )
    new_tournaments = new_tournaments.fillna("Unknown")  # name, surface, level
    return new_tournaments


def transform_players(df):
    # players
    with engine.connect() as conn:
        player_ids = {
            row[0] for row in conn.execute(text("SELECT player_id FROM players"))
        }

    df_winners = df.drop_duplicates("winner_id")
    new_winners = df_winners[~df_winners["winner_id"].isin(player_ids)]
    new_winners = new_winners[["winner_id", "winner_name", "winner_ioc", "winner_hand"]]
    new_winners = new_winners.rename(
        columns={
            "winner_id": "player_id",
            "winner_name": "name",
            "winner_ioc": "nationality",
            "winner_hand": "hand",
        }
    )

    df_losers = df.drop_duplicates("loser_id")
    new_losers = df_losers[~df_losers["loser_id"].isin(player_ids)]
    new_losers = new_losers[["loser_id", "loser_name", "loser_ioc", "loser_hand"]]
    new_losers = new_losers.rename(
        columns={
            "loser_id": "player_id",
            "loser_name": "name",
            "loser_ioc": "nationality",
            "loser_hand": "hand",
        }
    )

    new_players = pd.concat([new_winners, new_losers]).drop_duplicates("player_id")
    new_players["nationality"] = new_players["nationality"].fillna("Unknown")
    new_players["hand"] = new_players["hand"].fillna(
        "U"
    )  # sackmann data uses U for unknown hand
    return new_players


def transform_matches(df):
    # matches
    new_matches = df[
        ["match_id", "tourney_id", "round", "winner_id", "loser_id", "score"]
    ]
    new_matches = new_matches.rename(columns={"tourney_id": "tournament_id"})
    new_matches["match_date"] = df["tourney_date"]
    new_matches["score"] = new_matches["score"].fillna("Unknown")
    new_matches["round"] = new_matches["round"].fillna("Unknown")
    new_matches["round_int"] = new_matches["round"].map(lambda x: ROUND_ORDER.get(x))

    return new_matches


def transform_match_stats(df):
    winner_stats = df[
        [
            "match_id",
            "winner_id",
            "loser_id",
            "w_ace",
            "w_df",
            "w_svpt",
            "w_1stin",
            "w_1stwon",
            "w_2ndwon",
            "w_svgms",
            "w_bpsaved",
            "w_bpfaced",
        ]
    ].copy()
    winner_stats["won"] = True
    winner_stats["return_points"] = df["l_svpt"]
    winner_stats["first_serve_return_points"] = df["l_1stin"]
    winner_stats["first_serve_return_points_won"] = df["l_1stin"] - df["l_1stwon"]
    winner_stats["second_serve_return_points_won"] = (
        df["l_svpt"] - df["l_1stin"] - df["l_2ndwon"]
    )
    winner_stats["return_games"] = df["l_svgms"]
    winner_stats["break_points_converted"] = df["l_bpfaced"] - df["l_bpsaved"]
    winner_stats["break_points_chances"] = df["l_bpfaced"]
    winner_stats = winner_stats.rename(
        columns={
            "winner_id": "player_id",
            "loser_id": "opponent_id",
            "w_ace": "aces",
            "w_df": "double_faults",
            "w_svpt": "service_points",
            "w_1stin": "first_serves_in",
            "w_1stwon": "first_serve_points_won",
            "w_2ndwon": "second_serve_points_won",
            "w_svgms": "service_games",
            "w_bpsaved": "break_points_saved",
            "w_bpfaced": "break_points_faced",
        }
    )

    loser_stats = df[
        [
            "match_id",
            "loser_id",
            "winner_id",
            "l_ace",
            "l_df",
            "l_svpt",
            "l_1stin",
            "l_1stwon",
            "l_2ndwon",
            "l_svgms",
            "l_bpsaved",
            "l_bpfaced",
        ]
    ].copy()
    loser_stats["won"] = False
    loser_stats["return_points"] = df["w_svpt"]
    loser_stats["first_serve_return_points"] = df["w_1stin"]
    loser_stats["first_serve_return_points_won"] = df["w_1stin"] - df["w_1stwon"]
    loser_stats["second_serve_return_points_won"] = (
        df["w_svpt"] - df["w_1stin"] - df["w_2ndwon"]
    )
    loser_stats["return_games"] = df["w_svgms"]
    loser_stats["break_points_converted"] = df["w_bpfaced"] - df["w_bpsaved"]
    loser_stats["break_points_chances"] = df["w_bpfaced"]
    loser_stats = loser_stats.rename(
        columns={
            "loser_id": "player_id",
            "winner_id": "opponent_id",
            "l_ace": "aces",
            "l_df": "double_faults",
            "l_svpt": "service_points",
            "l_1stin": "first_serves_in",
            "l_1stwon": "first_serve_points_won",
            "l_2ndwon": "second_serve_points_won",
            "l_svgms": "service_games",
            "l_bpsaved": "break_points_saved",
            "l_bpfaced": "break_points_faced",
        }
    )

    match_stats = pd.concat([winner_stats, loser_stats], ignore_index=True)
    match_stats_columns = [
        "aces",
        "double_faults",
        "service_points",
        "first_serves_in",
        "first_serve_points_won",
        "second_serve_points_won",
        "service_games",
        "break_points_saved",
        "break_points_faced",
        "return_points",
        "first_serve_return_points",
        "first_serve_return_points_won",
        "second_serve_return_points_won",
        "return_games",
        "break_points_converted",
        "break_points_chances",
    ]
    match_stats["complete_stats"] = match_stats[match_stats_columns].notna().all(axis=1)
    return match_stats


def resolve_player_ids(df: pd.DataFrame, mask, conn) -> tuple[pd.DataFrame, list[dict]]:
    """
    Returns the df with winner_id and loser_id filled in,
    plus a list of new crosswalk entries to insert.
    """
    player_id_lookup = get_player_id_lookup_dict(conn)
    normalized_player_names = get_normalized_player_name_dict(conn)

    new_crosswalk_entries = []

    def resolve_single(api_id, name):
        if api_id in player_id_lookup:
            return player_id_lookup[api_id]

        # try fuzzy match against known players
        match, confidence, _ = process.extractOne(
            normalize_name(name),
            normalized_player_names.keys(),
            scorer=fuzz.token_sort_ratio,
        )

        if confidence >= 90:
            player_id = normalized_player_names[match]
            new_crosswalk_entries.append(
                {
                    "player_id": player_id,
                    "api_player_id": api_id,
                    "api_name": name,
                    "match_type": "fuzzy",
                    "confidence": confidence,
                }
            )
            # update local dict
            player_id_lookup[api_id] = player_id
            return player_id

        return None  # mark as None, will resolve later

    # apply function to winner and loser columns
    df.loc[mask, "winner_id"] = df.loc[mask].apply(
        lambda row: resolve_single(row["rapidapi_winner_id"], row["winner_name"]),
        axis=1,
    )
    df.loc[mask, "loser_id"] = df.loc[mask].apply(
        lambda row: resolve_single(row["rapidapi_loser_id"], row["loser_name"]), axis=1
    )

    return df, new_crosswalk_entries


def collect_pending_new_api_players(df, mask):
    pending = {}
    empty_winners = mask & df["winner_id"].isna()
    for api_id, group in df.loc[empty_winners].groupby("rapidapi_winner_id"):
        row = group.iloc[0]
        pending[api_id] = {
            "name": row["winner_name"],
            "nationality": row["winner_ioc"],
            "hand": row["winner_hand"],
        }
    empty_losers = mask & df["loser_id"].isna()
    for api_id, group in df.loc[empty_losers].groupby("rapidapi_loser_id"):
        row = group.iloc[0]
        if api_id not in pending:
            pending[api_id] = {
                "name": row["loser_name"],
                "nationality": row["loser_ioc"],
                "hand": row["loser_hand"],
            }
    return pending


def insert_new_api_players_and_lookup(conn, pending):
    api_to_pid = {}
    insert_into_players = text(
        """INSERT INTO players (name, nationality, hand) VALUES (:name, :nationality, :hand) RETURNING player_id"""
    )
    insert_into_player_id_lookup = text(
        """INSERT INTO player_id_lookup (api_player_id, player_id, api_name, match_type, confidence) VALUES (:api_player_id, :player_id, :api_name, :match_type, :confidence)"""
    )
    for api_id, data in pending.items():
        result = conn.execute(insert_into_players, data).fetchone()
        player_id = result.player_id
        api_to_pid[api_id] = player_id
        conn.execute(
            insert_into_player_id_lookup,
            {
                "api_player_id": api_id,
                "player_id": player_id,
                "api_name": data["name"],
                "match_type": "new",
                "confidence": -1,
            },
        )
    return api_to_pid


def fill_unresolved_api_player_ids(df, mask, api_to_pid):
    m = mask & df["winner_id"].isna()
    if m.any():
        df.loc[m, "winner_id"] = df.loc[m, "rapidapi_winner_id"].map(api_to_pid)
    m = mask & df["loser_id"].isna()
    if m.any():
        df.loc[m, "loser_id"] = df.loc[m, "rapidapi_loser_id"].map(api_to_pid)


def insert_fuzzy_matches_into_lookup(fuzzy_matches, conn):
    if not fuzzy_matches:
        return
    insert_stmt = text(
        """
        INSERT INTO player_id_lookup 
            (player_id, api_player_id, api_name, match_type, confidence)
        VALUES 
            (:player_id, :api_player_id, :api_name, :match_type, :confidence)
        """
    )
    for entry in fuzzy_matches:
        conn.execute(insert_stmt, entry)


def transform_raw_matches(sackmann_only: bool = False):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
            SELECT r.* FROM raw_matches r
            WHERE NOT EXISTS (
                SELECT 1 FROM matches m WHERE m.match_id = r.match_id
            )
        """),
            conn,
        )
        logger.info("Loaded raw_matches from database")

    if df.empty:
        logger.info("No new matches found for transform.py")
        return

    if sackmann_only:
        df = df[df["source"] == "sackmann"]
    else:
        # processing for rapidapi data only
        mask = df["source"] == "rapidapi"

        # normalize tourney_id, surface, match date
        df.loc[mask, "tourney_id"] = df.loc[mask, "rapidapi_tournament_id"].map(str)
        df.loc[mask, "surface"] = df.loc[mask, "surface"].map(map_surface_names)
        df.loc[mask, "tourney_date"] = df.loc[mask, "match_date"]

        with engine.connect() as conn:
            df, new_crosswalk_entries = resolve_player_ids(df, mask, conn)

    # ===================================================================================
    # processing for all data, both sackmann and rapidapi

    # this handles some errors in sackmann data where the same player is on both sides of the match, 7 cases
    # will also protect against this happening in future data
    len_before_drop = len(df)
    df = df[df["winner_id"] != df["loser_id"]]
    if len(df) == 0:
        logger.warning(
            f"No matches found after winner != loser: {len_before_drop} matches dropped"
        )
        return

    logger.info(f"Processing {len(df)} matches")

    new_tournaments = transform_tournaments(df)

    logger.info("Finished processing raw matches")
    # ===================================================================================
    with engine.begin() as conn:
        logger.info("Loading match data into database...")
        new_tournaments.to_sql("tournaments", conn, if_exists="append", index=False)

        if not sackmann_only:
            pending = collect_pending_new_api_players(df, mask)
            if pending:
                api_to_pid = insert_new_api_players_and_lookup(conn, pending)
                fill_unresolved_api_player_ids(df, mask, api_to_pid)
            insert_fuzzy_matches_into_lookup(new_crosswalk_entries, conn)
        else:
            new_players = transform_players(df)
            new_players.to_sql("players", conn, if_exists="append", index=False)

        new_matches = transform_matches(df)
        match_stats = transform_match_stats(df)

        new_matches.to_sql("matches", conn, if_exists="append", index=False)
        match_stats.to_sql("match_stats", conn, if_exists="append", index=False)
    logger.info("Loaded match data into database")


if __name__ == "__main__":
    transform_raw_matches()
