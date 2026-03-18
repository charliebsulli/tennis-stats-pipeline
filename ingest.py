import json
import os
import time
from dotenv import load_dotenv
import requests
from datetime import date, timedelta
import pandas as pd

load_dotenv()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY not found in environment variables")

BASE_URL = "https://tennisapi1.p.rapidapi.com"

def query_by_date(category, date: date):
    response = get_matches_by_category_and_date(category, date)
    daily_matches = response.json()
    df = process_daily_matches_into_df(daily_matches)
    # make the requests to each match id in the df, filling in the other stats data
    df = fill_match_stats(df)
    # add the dataframe to the matches table
    df.to_csv("test.csv", index=False)


def get_matches_by_category_and_date(category, date: date):
    category_id = category # TODO
    day = date.day
    month = date.month
    year = date.year
    url = BASE_URL + "/api/tennis/category/" + category_id + "/events/" + str(day) + "/" + str(month) + "/" + str(year)

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "tennisapi1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response


def process_daily_matches_into_df(matches):
    # decode the json object into relevant match data and put it into a dataframe
    rows = []
    for i, match in enumerate(matches["events"][:3]): # TODO 3 for now
        print(f"extracting match {i}")
        rows.append(extract_match(match))
    df = pd.DataFrame(rows)
    return df


def extract_match(match: dict):
    # check that the match is complete, will need to look at the statuses to check this for sure
    if match["status"]["code"] != 100:
        return {}

    winner_code = match["winnerCode"]
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
        "rapidapi_match_id": match["id"],
        "winner_team": winnerTeam,
        # for now I treat each year of a tournament as separate (like Sackmann)
        # this is consistent with "seasons" from the API
        "tourney_id": match["season"]["id"],
        # an appropriate name comes from uniqueTournament
        "tourney_name": match["tournament"]["uniqueTournament"]["name"],
        "surface": match["tournament"]["uniqueTournament"]["groundType"],
        "match_date": match["startTimestamp"],
        "winner_id": match[winnerTeam]["id"],
        # winner_seed TODO
        "winner_name": match[winnerTeam]["name"],
        "winner_ioc": match[winnerTeam]["country"]["alpha3"],
        # hand, height, age -- for existing players these are already filled
        # but will need to find them for new players
        "loser_id": match[loserTeam]["id"],
        "loser_name": match[loserTeam]["name"],
        "loser_ioc": match[loserTeam]["country"]["alpha3"],
        "score": compute_score(match[winnerScore], match[loserScore]),
        # best_of?
        "round": match["roundInfo"]["name"],
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
        stats = parse_match_stats(response.json(), row["winner_team"])
        stats["rapidapi_match_id"] = row["rapidapi_match_id"]
        stats_rows.append(stats)
        time.sleep(0.5)
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


def get_match_stats_by_id(id):
    url = BASE_URL + "/api/tennis/event/" + str(id) + "/statistics"

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "tennisapi1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response

if __name__ == "__main__":
    query_date = date.today() - timedelta(days=1)
    query_by_date("3", query_date)