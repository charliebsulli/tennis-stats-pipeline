import time
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from api_calls import get_matches_by_category_and_date, get_match_stats_by_id
from db_connection import get_connection

ATP_CATEGORY_ID = "3"
CHALLENGER_CATEGORY_ID = "72"

def query_by_date(category, date: date) -> pd.DataFrame:
    response = get_matches_by_category_and_date(category, date)
    daily_matches = response.json()
    df = process_daily_matches_into_df(daily_matches)
    df = fill_match_stats(df)
    return df


def process_daily_matches_into_df(matches):
    # decode the json object into relevant match data and put it into a dataframe
    rows = [extract_match(match) for match in matches["events"]]
    df = pd.DataFrame(rows).dropna(subset=["rapidapi_match_id"])
    id_columns = ['rapidapi_match_id', 'rapidapi_tournament_id', 'rapidapi_winner_id', 'rapidapi_loser_id']
    df[id_columns] = df[id_columns].astype('Int64')
    return df


def extract_match(match: dict):
    # check that the match is complete, will need to look at the statuses to check this for sure
    if match.get("status", {}).get("code") != 100:
        return {} # these will be dropped

    if len(match.get("homeTeam", {}).get("subTeams", [])) > 0:
        return {} # doubles match

    winner_code = match.get("winnerCode")
    if winner_code == 1:
        winnerTeam = "homeTeam"
        loserTeam = "awayTeam"
        winnerScore = "homeScore"
        loserScore = "awayScore"
    else:
        winnerTeam = "awayTeam"
        loserTeam = "homeTeam"
        winnerScore = "awayScore"
        loserScore = "homeScore"

    return {
        # to look up detailed stats
        "rapidapi_match_id": match.get("id"),
        "winner_team": winnerTeam,
        # for now I treat each year of a tournament as separate (like Sackmann)
        # this is consistent with "seasons" from the API
        "rapidapi_tournament_id": match.get("season", {}).get("id"),
        # an appropriate name comes from uniqueTournament
        "tourney_name": match.get("tournament", {}).get("uniqueTournament", {}).get("name"),
        "surface": match.get("tournament", {}).get("uniqueTournament", {}).get("groundType"),
        "match_date": match.get("startTimestamp"),
        "rapidapi_winner_id": match.get(winnerTeam, {}).get("id"),
        # winner_seed TODO
        "winner_name": match.get(winnerTeam, {}).get("name"),
        "winner_ioc": match.get(winnerTeam, {}).get("country", {}).get("alpha3"),
        # hand, height, age -- for existing players these are already filled
        # but will need to find them for new players
        "rapidapi_loser_id": match.get(loserTeam, {}).get("id"),
        "loser_name": match.get(loserTeam, {}).get("name"),
        "loser_ioc": match.get(loserTeam, {}).get("country", {}).get("alpha3"),
        "score": compute_score(match.get(winnerScore), match.get(loserScore)),
        # best_of?
        "round": match.get("roundInfo", {}).get("name"),
        # minutes
    }


def compute_score(winnerScore, loserScore):
    win_games_list = [
        winnerScore.get("period1"),
        winnerScore.get("period2"),
        winnerScore.get("period3"),
        winnerScore.get("period4"),
        winnerScore.get("period5"),
    ]
    
    lose_games_list = [
        loserScore.get("period1"),
        loserScore.get("period2"),
        loserScore.get("period3"),
        loserScore.get("period4"),
        loserScore.get("period5"),
    ]

    score_str = ""
    for winner, loser in zip(win_games_list, lose_games_list):
        if winner is None or loser is None:
            break
        score_str += f"{winner}-{loser} "
    return score_str.rstrip(" ")


def fill_match_stats(df):
    stats_rows = []
    for idx, row in df.iterrows():
        response = get_match_stats_by_id(row["rapidapi_match_id"])
        if response.status_code == 200:
            stats = parse_match_stats(response.json(), row["winner_team"])
            stats["rapidapi_match_id"] = row["rapidapi_match_id"]
            stats_rows.append(stats)
            time.sleep(0.2) # to avoid hitting rate limits
        else:
            print("Failed on this row:")
            print(row)
    stats_df = pd.DataFrame(stats_rows)
    return pd.merge(df, stats_df, on="rapidapi_match_id", how="left")


def parse_match_stats(response_json, winner_team):
    # get stats for the entire match
    res_stats = next(p for p in response_json["statistics"] if p["period"] == "ALL")
    # index all the stat objects in a statistics_list by key to make the stats easy to access
    res_stats_dict = {}
    for group in res_stats["groups"]:
        for stat_item in group["statisticsItems"]:
            res_stats_dict[stat_item["key"]] = stat_item

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

    return {
        "w_ace": res_stats_dict.get("aces", {}).get(winner_value),
        "w_df": res_stats_dict.get("doubleFaults", {}).get(winner_value),
        "w_svpt": res_stats_dict.get("firstServePointsAccuracy", {}).get(winner_total) + res_stats_dict.get("secondServePointsAccuracy", {}).get(winner_total),
        "w_1stIn": res_stats_dict.get("firstServeAccuracy", {}).get(winner_value),
        "w_1stWon": res_stats_dict.get("firstServePointsAccuracy", {}).get(winner_value),
        "w_2ndWon": res_stats_dict.get("secondServePointsAccuracy", {}).get(winner_value),
        "w_SvGms": res_stats_dict.get("serviceGamesTotal", {}).get(winner_value),
        "w_bpSaved": res_stats_dict.get("breakPointsSaved", {}).get(winner_value),
        "w_bpFaced": res_stats_dict.get("breakPointsSaved", {}).get(winner_total),

        "l_ace": res_stats_dict.get("aces", {}).get(loser_value),
        "l_df": res_stats_dict.get("doubleFaults", {}).get(loser_value),
        "l_svpt": res_stats_dict.get("firstServePointsAccuracy", {}).get(loser_total) + res_stats_dict.get("secondServePointsAccuracy", {}).get(loser_total),
        "l_1stIn": res_stats_dict.get("firstServeAccuracy", {}).get(loser_value),
        "l_1stWon": res_stats_dict.get("firstServePointsAccuracy", {}).get(loser_value),
        "l_2ndWon": res_stats_dict.get("secondServePointsAccuracy", {}).get(loser_value),
        "l_SvGms": res_stats_dict.get("serviceGamesTotal", {}).get(loser_value),
        "l_bpSaved": res_stats_dict.get("breakPointsSaved", {}).get(loser_value),
        "l_bpFaced": res_stats_dict.get("breakPointsSaved", {}).get(loser_total),
    }


# https://pandas.pydata.org/docs/user_guide/io.html#insertion-method
def insert_or_ignore(table, conn, keys, data_iter):
    conn.executemany(f"INSERT OR IGNORE INTO {table.name} ({', '.join(keys)}) "
                    f"VALUES ({', '.join(['?' for key in keys])})", list(data_iter))


def ingest_by_date(category, date):
    df = query_by_date(category, date)
    
    df.drop(columns=["winner_team"], inplace=True)
    df['source'] = 'rapidapi'
    df['time_added'] = datetime.now(timezone.utc).isoformat()
    
    conn = get_connection()
    df.to_sql("raw_matches", conn, if_exists="append", index=False, method=insert_or_ignore)
    conn.close()

    print(f"Added {len(df)} matches for date {date} and category {category}")


if __name__ == "__main__":
    query_date = date.today() - timedelta(days=14)
    ingest_by_date(ATP_CATEGORY_ID, query_date)
    ingest_by_date(CHALLENGER_CATEGORY_ID, query_date)
