import logging
import unicodedata

import pandas as pd
from rapidfuzz import fuzz, process
from sqlalchemy import text

logger = logging.getLogger(__name__)


def resolve_player_ids(
    df: pd.DataFrame,
    mask,
    conn,
    source: str = "rapidapi",
    winner_id_col: str = "rapidapi_winner_id",
    loser_id_col: str = "rapidapi_loser_id",
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Returns the df with winner_id and loser_id filled in,
    plus a list of new crosswalk entries to insert.

    The crosswalk is looked up per source: two APIs can hand out the same
    integer id for different people, so an id is only meaningful together
    with the source it came from.
    """
    player_id_lookup = get_player_id_lookup_dict(conn, source)
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
                    "source": source,
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
        lambda row: resolve_single(row[winner_id_col], row["winner_name"]),
        axis=1,
    )
    df.loc[mask, "loser_id"] = df.loc[mask].apply(
        lambda row: resolve_single(row[loser_id_col], row["loser_name"]), axis=1
    )

    return df, new_crosswalk_entries


def collect_pending_new_api_players(
    df,
    mask,
    winner_id_col: str = "rapidapi_winner_id",
    loser_id_col: str = "rapidapi_loser_id",
):
    pending = {}
    empty_winners = mask & df["winner_id"].isna()
    for api_id, group in df.loc[empty_winners].groupby(winner_id_col):
        row = group.iloc[0]
        pending[api_id] = {
            "name": row["winner_name"],
            "nationality": row["winner_ioc"],
            "hand": row["winner_hand"],
        }
    empty_losers = mask & df["loser_id"].isna()
    for api_id, group in df.loc[empty_losers].groupby(loser_id_col):
        row = group.iloc[0]
        if api_id not in pending:
            pending[api_id] = {
                "name": row["loser_name"],
                "nationality": row["loser_ioc"],
                "hand": row["loser_hand"],
            }
    return pending


def insert_new_api_players_and_lookup(conn, pending, source: str = "rapidapi"):
    api_to_pid = {}
    insert_into_players = text(
        """INSERT INTO players (name, nationality, hand) VALUES (:name, :nationality, :hand) RETURNING player_id"""
    )
    insert_into_player_id_lookup = text(
        """INSERT INTO player_id_lookup (api_player_id, player_id, source, api_name, match_type, confidence) VALUES (:api_player_id, :player_id, :source, :api_name, :match_type, :confidence)"""
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
                "source": source,
                "api_name": data["name"],
                "match_type": "new",
                "confidence": -1,
            },
        )
    return api_to_pid


def fill_unresolved_api_player_ids(
    df,
    mask,
    api_to_pid,
    winner_id_col: str = "rapidapi_winner_id",
    loser_id_col: str = "rapidapi_loser_id",
):
    m = mask & df["winner_id"].isna()
    if m.any():
        df.loc[m, "winner_id"] = df.loc[m, winner_id_col].map(api_to_pid)
    m = mask & df["loser_id"].isna()
    if m.any():
        df.loc[m, "loser_id"] = df.loc[m, loser_id_col].map(api_to_pid)


def insert_fuzzy_matches_into_lookup(fuzzy_matches, conn):
    if not fuzzy_matches:
        return
    insert_stmt = text(
        """
        INSERT INTO player_id_lookup 
            (player_id, api_player_id, source, api_name, match_type, confidence)
        VALUES 
            (:player_id, :api_player_id, :source, :api_name, :match_type, :confidence)
        """
    )
    for entry in fuzzy_matches:
        conn.execute(insert_stmt, entry)


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = name.replace("-", " ")
    return name


def get_player_id_lookup_dict(conn, source: str = "rapidapi"):
    result = conn.execute(
        text(
            "SELECT api_player_id, player_id FROM player_id_lookup WHERE source = :source"
        ),
        {"source": source},
    ).fetchall()
    return {row.api_player_id: row.player_id for row in result}


def get_normalized_player_name_dict(conn):
    rows = conn.execute(text("SELECT player_id, name FROM players")).fetchall()
    return {normalize_name(row.name): row.player_id for row in rows}
