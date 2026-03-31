import logging
from datetime import date

import pandas as pd
from sqlalchemy import text

from aggregate import compute_head_to_head, compute_player_surface_stats
from constants import ATP_CATEGORY_ID, CHALLENGER_CATEGORY_ID
from db_connection import engine
from ingest import ingest_by_date
from logging_config import setup_logging
from transform import transform_raw_matches

setup_logging()

logger = logging.getLogger(__name__)


def get_completed_dates() -> set:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT backfill_date FROM backfill_progress"))
        return {row.backfill_date for row in rows}


def mark_date_complete(date):
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO backfill_progress (backfill_date, completed_at)
            VALUES (:date, NOW())
            ON CONFLICT DO NOTHING
        """),
            {"date": date},
        )


def backfill_data(start_date, end_date):
    all_dates = pd.date_range(start_date, end_date)
    completed = get_completed_dates()
    remaining = [d for d in all_dates if d.date() not in completed]

    logger.info(
        f"Backfill: {len(completed)} dates already done, {len(remaining)} remaining"
    )

    for date in remaining:  # noqa: F402
        try:
            ingest_by_date(ATP_CATEGORY_ID, date)
            ingest_by_date(CHALLENGER_CATEGORY_ID, date)
            transform_raw_matches()
            mark_date_complete(date.date())
            logger.info(
                f"Completed {date.date()} ({remaining.index(date) + 1}/{len(remaining)})"
            )
        except Exception as e:
            logger.error(f"Failed on {date.date()}: {e}")
            raise  # stop the backfill, don't skip silently

    logger.info("Backfill complete, running aggregations...")
    compute_player_surface_stats()
    compute_head_to_head()


if __name__ == "__main__":
    backfill_data(date(2026, 1, 1), date(2026, 3, 24))
    # TODO if I want to run this in deployment I should make this command line args
    # TODO backfill will hit api rate limit
    # TODO HTTP read timeout
