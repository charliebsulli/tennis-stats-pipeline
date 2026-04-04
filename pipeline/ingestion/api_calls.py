import logging
import os
import time
from datetime import date

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY not found in environment variables")

BASE_URL = "https://tennisapi1.p.rapidapi.com"

REQUEST_TIMEOUT_SEC = 10
READ_TIMEOUT_RETRIES = 5

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "tennisapi1.p.rapidapi.com",
    "Content-Type": "application/json",
}


def make_request(url):
    for attempt in range(READ_TIMEOUT_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SEC)
            response.raise_for_status()
            return response
        except requests.exceptions.ReadTimeout:
            logger.warning(
                "Read timeout for %s (attempt %s/%s)",
                url,
                attempt + 1,
                READ_TIMEOUT_RETRIES,
            )
            if attempt < READ_TIMEOUT_RETRIES - 1:
                time.sleep(0.6 * (attempt + 1))
        except requests.HTTPError:
            logger.exception("Request failed for %s", url)
            return None
        except requests.RequestException:
            logger.exception("Request failed for %s", url)
            return None

    logger.error("Read timeout after %s attempts for %s", READ_TIMEOUT_RETRIES, url)
    return None


def get_matches_by_category_and_date(category, date: date):
    day = date.day
    month = date.month
    year = date.year
    url = f"{BASE_URL}/api/tennis/category/{category}/events/{day}/{month}/{year}"

    return make_request(url)


def get_match_stats_by_id(id):
    url = f"{BASE_URL}/api/tennis/event/{id}/statistics"

    return make_request(url)


def get_rankings():
    url = f"{BASE_URL}/api/tennis/rankings/atp"

    return make_request(url)
