import requests
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY not found in environment variables")

BASE_URL = "https://tennisapi1.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "tennisapi1.p.rapidapi.com",
    "Content-Type": "application/json"
}

def get_matches_by_category_and_date(category, date: date):
    category_id = category # TODO
    day = date.day
    month = date.month
    year = date.year
    url = BASE_URL + "/api/tennis/category/" + category_id + "/events/" + str(day) + "/" + str(month) + "/" + str(year)

    response = requests.get(url, headers=HEADERS)
    return response


def get_match_stats_by_id(id):
    url = BASE_URL + "/api/tennis/event/" + str(id) + "/statistics"
    response = requests.get(url, headers=HEADERS)
    return response


def get_rankings():
    url = BASE_URL + "/api/tennis/rankings/atp"
    response = requests.get(url, headers=HEADERS)
    return response