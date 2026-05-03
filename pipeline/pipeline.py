import argparse
import logging
from datetime import date, timedelta

from pipeline.aggregate.elo import update_elo
from pipeline.aggregate.form import compute_form
from pipeline.aggregate.head_to_head import compute_head_to_head
from pipeline.aggregate.surface_stats import compute_surface_stats
from pipeline.db.db_connection import engine
from pipeline.ingestion.ingest import ingest_daily
from pipeline.logging_config import setup_logging
from pipeline.transform.player_id_helper import insert_new_api_players
from pipeline.transform.transform import transform_raw_matches

logger = logging.getLogger(__name__)


def run_pipeline(run_date):
    logger.info("Starting pipeline run")
    ingest_daily(run_date)
    with engine.connect() as conn:
        insert_new_api_players(conn)
    # transform_raw_matches()
    # compute_surface_stats()
    # compute_head_to_head()
    # compute_form()
    # update_elo()
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
