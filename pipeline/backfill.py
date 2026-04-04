import argparse
import logging
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import text

from db.db_connection import engine
from ingestion.ingest import ingest_daily
from logging_config import setup_logging

logger = logging.getLogger(__name__)


def backfill(start_date, end_date):
    all_dates = pd.date_range(start_date, end_date)
    completed = get_completed_dates()
    remaining = [d for d in all_dates if d.date() not in completed]

    logger.info(
        f"Backfill: {len(completed)} dates already done, {len(remaining)} remaining"
    )

    date_count = 0
    for run_date in remaining:
        logger.info(f"Starting {run_date.date()}")
        try:
            ingest_daily(run_date)
            mark_date_complete(run_date.date())
            logger.info(
                f"Completed {run_date.date()} ({remaining.index(run_date) + 1}/{len(remaining)})"
            )
            date_count += 1
        except Exception as e:
            logger.error(f"Failed on {run_date.date()}: {e}")
            raise
        if (
            date_count > 90
        ):  # 90 days worth of matches will stay safely below daily API limit
            return

    logger.info("Backfill complete")


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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=date(2024, 12, 26),
        help="Start date for the backfill (YYYY-MM-DD). Defaults to 2024-12-26.",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="End date for the backfill (YYYY-MM-DD). Defaults to yesterday.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    backfill(args.start_date, args.end_date)
