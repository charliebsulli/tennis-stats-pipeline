import argparse
import logging
from datetime import date, timedelta

from aggregate.elo import update_elo
from aggregate.form import compute_form
from aggregate.head_to_head import compute_head_to_head
from aggregate.surface_stats import compute_surface_stats
from ingestion.ingest import ingest_daily
from logging_config import setup_logging
from transform.transform import transform_raw_matches

logger = logging.getLogger(__name__)


def run_pipeline(run_date):
    logger.info("Starting pipeline run")
    ingest_daily(run_date)
    transform_raw_matches()
    compute_surface_stats()
    compute_head_to_head()
    compute_form()
    update_elo()
    logger.info("Pipeline complete")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="Date to run pipeline for (YYYY-MM-DD). Defaults to yesterday.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    run_pipeline(args.date)
