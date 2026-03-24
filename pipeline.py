import argparse
import logging
from datetime import date, datetime, timedelta

from aggregate import compute_head_to_head, compute_player_surface_stats
from ingest import ATP_CATEGORY_ID, CHALLENGER_CATEGORY_ID, ingest_by_date
from logging_config import setup_logging
from transform import transform_raw_matches

setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        type=str,
        help="The date for which to query data (YYYY-MM-DD).",
    )
    args = parser.parse_args()

    if args.date:
        try:
            query_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.exception(
                f"Error: Invalid date format for --date. Please use YYYY-MM-DD."
            )
            exit(1)

    logger.info(f"Processing data for date: {query_date}")

    # ingest new data from API
    ingest_by_date(ATP_CATEGORY_ID, query_date)
    ingest_by_date(CHALLENGER_CATEGORY_ID, query_date)

    transform_raw_matches()

    compute_player_surface_stats()
    compute_head_to_head()
