import logging
import time
from datetime import date, datetime, timezone

import pandas as pd
import requests
from psycopg2.extras import execute_values

from pipeline.constants import ATP_CATEGORY_ID, CHALLENGER_CATEGORY_ID
from pipeline.db.db_connection import engine
from pipeline.ingestion.api_calls import (
    get_match_stats_by_id,
    get_matches_by_category_and_date,
)

logger = logging.getLogger(__name__)


def ingest_daily(date):
    ingest_by_date(ATP_CATEGORY_ID, date)
    ingest_by_date(CHALLENGER_CATEGORY_ID, date)


def ingest_by_date(category, date):
    df = query_by_date(category, date)
    if df.empty:
        logger.info(f"No data found for date {date}")
        return

    df.drop(columns=["winner_team"], inplace=True)
    df["source"] = "rapidapi"
    df["time_added"] = datetime.now(timezone.utc).isoformat()
    df["match_date"] = df["match_date"].map(lambda x: date.fromtimestamp(x))
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates("rapidapi_match_id")

    logger.info(f"Attempting to insert {len(df)} matches")

    with engine.connect() as conn:
        rows = df.to_sql(
            "raw_matches",
            conn,
            if_exists="append",
            index=False,
            method=insert_or_ignore,
        )
        logger.info(f"Inserted {rows} matches for date {date} and category {category}")


def insert_or_ignore(table, conn, keys, data_iter):
    raw_conn = conn.connection
    rows = list(data_iter)

    if not rows:
        return 0

    columns = ", ".join(keys)

    query = f"""
        INSERT INTO {table.name} ({columns})
        VALUES %s
        ON CONFLICT (rapidapi_match_id) DO NOTHING
        RETURNING 1
    """

    with raw_conn.cursor() as cur:
        execute_values(cur, query, rows)
        inserted = cur.fetchall()

    return len(inserted)


def query_by_date(category, date: date) -> pd.DataFrame:
    response = get_matches_by_category_and_date(category, date)
    if response is None:
        logger.warning(f"Failed to get matches for category {category} on date {date}")
        return pd.DataFrame()
    try:
        daily_matches = response.json()
    except requests.exceptions.JSONDecodeError as e:
        logger.exception(f"Failed to decode JSON response: {e}")
        return pd.DataFrame()
    df = process_daily_matches_into_df(daily_matches)
    if df.empty:
        logger.info(f"Matches not found for category {category} on date {date}")
        return pd.DataFrame()
    df = fill_match_stats(df)
    return df


def process_daily_matches_into_df(matches):
    # decode the json object into relevant match data and put it into a dataframe
    events = matches.get("events")
    if events is None:
        return pd.DataFrame()
    logger.info(f"Extracting match data for {len(events)} matches")
    rows = [extract_match(match) for match in events]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()

    # require all of these columns for a match to be valid
    id_columns = [
        "rapidapi_match_id",
        "rapidapi_tournament_id",
        "rapidapi_winner_id",
        "rapidapi_loser_id",
    ]
    df = df.dropna(subset=id_columns)
    df[id_columns] = df[id_columns].astype(
        "Int64"
    )  # make sure ids are ints, not floats
    logger.info(f"{len(df)} valid matches found")
    return df


def extract_match(match: dict):
    if match.get("status", {}).get("code") != 100:
        return {}  # these will be dropped

    if len(match.get("homeTeam", {}).get("subTeams", [])) > 0:
        return {}  # doubles match

    winner_code = match.get("winnerCode")
    if winner_code == 1:
        winner_team = "homeTeam"
        loser_team = "awayTeam"
        winner_score = "homeScore"
        loser_score = "awayScore"
    elif winner_code == 2:
        winner_team = "awayTeam"
        loser_team = "homeTeam"
        winner_score = "awayScore"
        loser_score = "homeScore"
    else:
        logger.warning(f"Unexpected winnerCode: {winner_code}")
        return {}

    return {
        "rapidapi_match_id": match.get("id"),
        "winner_team": winner_team,
        "rapidapi_tournament_id": match.get("season", {}).get(
            "id"
        ),  # a season is one edition of a tournament
        "tourney_name": match.get("tournament", {})
        .get("uniqueTournament", {})
        .get("name"),  # an appropriate name comes from uniqueTournament
        "surface": match.get("tournament", {})
        .get("uniqueTournament", {})
        .get("groundType"),
        "match_date": match.get("startTimestamp"),
        "rapidapi_winner_id": match.get(winner_team, {}).get("id"),
        "winner_name": match.get(winner_team, {}).get("name"),
        "winner_ioc": match.get(winner_team, {}).get("country", {}).get("alpha3"),
        "rapidapi_loser_id": match.get(loser_team, {}).get("id"),
        "loser_name": match.get(loser_team, {}).get("name"),
        "loser_ioc": match.get(loser_team, {}).get("country", {}).get("alpha3"),
        "score": compute_score(match.get(winner_score), match.get(loser_score)),
        "round": match.get("roundInfo", {}).get("name"),
    }


def compute_score(winner_score, loser_score) -> str:
    score_parts = []
    for i in range(1, 6):  # Iterate through period1 to period5
        period_key = f"period{i}"
        winner_games = winner_score.get(period_key)
        loser_games = loser_score.get(period_key)

        if winner_games is None or loser_games is None:
            break
        score_parts.append(f"{winner_games}-{loser_games}")

    return " ".join(score_parts)


def fill_match_stats(df):
    stats_rows = []
    for idx, row in df.iterrows():
        response = get_match_stats_by_id(row["rapidapi_match_id"])
        if response is None:
            logger.warning(
                f"Match stats not found for match {row['rapidapi_match_id']}"
            )
        else:
            try:
                response_json = response.json()
                stats = parse_match_stats(response_json, row["winner_team"])
                stats["rapidapi_match_id"] = row["rapidapi_match_id"]
                stats_rows.append(stats)
            except requests.exceptions.JSONDecodeError as e:
                logger.exception(
                    f"Failed to decode JSON response: {e} for match {row['rapidapi_match_id']}"
                )
        logger.info(f"Filled detailed stats for match {row['rapidapi_match_id']}")
        time.sleep(0.2)  # to avoid hitting rate limits

    if len(stats_rows) == 0:
        logger.warning(
            "No detailed stats found for any match, inserting without detailed stats."
        )
        return df
    stats_df = pd.DataFrame(stats_rows)
    return pd.merge(df, stats_df, on="rapidapi_match_id", how="left")


def parse_match_stats(response_json, winner_team):
    stats = response_json.get("statistics")
    if stats is None:
        logger.info("Match stats not found")
        return {}

    try:
        res_stats = next(p for p in response_json["statistics"] if p["period"] == "ALL")
    except StopIteration:
        logger.exception("Period ALL not found in stats")
        return {}

    # index all the stat objects in a statistics_list by key to make the stats easy to access
    try:
        res_stats_dict = {}
        for group in res_stats["groups"]:
            for stat_item in group["statisticsItems"]:
                res_stats_dict[stat_item["key"]] = stat_item
    except KeyError as e:
        logger.exception(f"Unexpected match stats dict structure: {e}")
        return {}

    # API uses home/away instead of winner/loser
    if winner_team == "homeTeam":
        winner_value = "homeValue"
        loser_value = "awayValue"
        winner_total = "homeTotal"
        loser_total = "awayTotal"
    else:
        winner_value = "awayValue"
        loser_value = "homeValue"
        winner_total = "awayTotal"
        loser_total = "homeTotal"

    try:
        w_svpt = res_stats_dict.get("firstServePointsAccuracy", {}).get(
            winner_total
        ) + res_stats_dict.get("secondServePointsAccuracy", {}).get(winner_total)
        l_svpt = res_stats_dict.get("firstServePointsAccuracy", {}).get(
            loser_total
        ) + res_stats_dict.get("secondServePointsAccuracy", {}).get(loser_total)
    except TypeError:
        logger.exception("Setting w_svpt, l_svpt to None: missing necessary value")
        w_svpt = None
        l_svpt = None

    return {
        "w_ace": res_stats_dict.get("aces", {}).get(winner_value),
        "w_df": res_stats_dict.get("doubleFaults", {}).get(winner_value),
        "w_svpt": w_svpt,
        "w_1stIn": res_stats_dict.get("firstServeAccuracy", {}).get(winner_value),
        "w_1stWon": res_stats_dict.get("firstServePointsAccuracy", {}).get(
            winner_value
        ),
        "w_2ndWon": res_stats_dict.get("secondServePointsAccuracy", {}).get(
            winner_value
        ),
        "w_SvGms": res_stats_dict.get("serviceGamesTotal", {}).get(winner_value),
        "w_bpSaved": res_stats_dict.get("breakPointsSaved", {}).get(winner_value),
        "w_bpFaced": res_stats_dict.get("breakPointsSaved", {}).get(winner_total),
        "l_ace": res_stats_dict.get("aces", {}).get(loser_value),
        "l_df": res_stats_dict.get("doubleFaults", {}).get(loser_value),
        "l_svpt": l_svpt,
        "l_1stIn": res_stats_dict.get("firstServeAccuracy", {}).get(loser_value),
        "l_1stWon": res_stats_dict.get("firstServePointsAccuracy", {}).get(loser_value),
        "l_2ndWon": res_stats_dict.get("secondServePointsAccuracy", {}).get(
            loser_value
        ),
        "l_SvGms": res_stats_dict.get("serviceGamesTotal", {}).get(loser_value),
        "l_bpSaved": res_stats_dict.get("breakPointsSaved", {}).get(loser_value),
        "l_bpFaced": res_stats_dict.get("breakPointsSaved", {}).get(loser_total),
    }
