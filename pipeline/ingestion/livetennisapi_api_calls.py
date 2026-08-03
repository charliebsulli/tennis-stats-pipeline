import logging
import os
import time

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

BASE_URL = "https://api.livetennisapi.com/api/public/v1"

REQUEST_TIMEOUT_SEC = 10
READ_TIMEOUT_RETRIES = 5

# Provider caps limit at 200.
PAGE_SIZE = 200


def get_api_key():
    """
    Read the key lazily so an unconfigured install stays importable.

    api_calls.py raises at import time because the RapidAPI source is
    required. This source is optional, so a missing key is not an error:
    ingestion is skipped instead.
    """
    return os.getenv("LIVETENNISAPI_KEY")


def is_enabled():
    return bool(get_api_key())


def make_request(url, params=None):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_api_key()}",
    }

    for attempt in range(READ_TIMEOUT_RETRIES):
        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SEC
            )
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


def get_history_matches(from_date, to_date, limit=PAGE_SIZE, offset=0):
    """
    One page of completed matches in a date window, newest first.

    from_date/to_date are dates; the provider takes YYYY-MM-DD.
    """
    url = f"{BASE_URL}/history/matches"
    params = {
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "limit": limit,
        "offset": offset,
    }

    return make_request(url, params=params)


def iter_history_matches(from_date, to_date):
    """
    Page through the completed-match listing for a date window.

    Paging stops on meta.has_more rather than on a short page: the provider
    documents that a filtered page can be shorter than the limit while later
    pages still hold matches.
    """
    offset = 0

    while True:
        response = get_history_matches(from_date, to_date, offset=offset)
        if response is None:
            logger.warning(
                "Stopping history paging for %s..%s after a failed request",
                from_date,
                to_date,
            )
            return

        payload = response.json()
        page = payload.get("data") or []
        for match in page:
            yield match

        meta = payload.get("meta") or {}
        if not meta.get("has_more"):
            return

        offset += len(page)
        if not page:
            # has_more is set but the page is empty; stop rather than loop.
            logger.warning("Empty page with has_more set at offset %s", offset)
            return
