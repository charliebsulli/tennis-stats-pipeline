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

# wrapper to check status
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.HTTPError as e:
        print(f"Request failed: {e}")
        return None


def get_matches_by_category_and_date(category, date: date):
    category_id = category # TODO
    day = date.day
    month = date.month
    year = date.year
    url = f"{BASE_URL}/api/tennis/category/{category_id}/events/{day}/{month}/{year}"
    
    return make_request(url)


def get_match_stats_by_id(id):
    url = f"{BASE_URL}/api/tennis/event/{id}/statistics"
    
    return make_request(url)


def get_rankings():
    url = f"{BASE_URL}/api/tennis/rankings/atp"
    
    return make_request(url)