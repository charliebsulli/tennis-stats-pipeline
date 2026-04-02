import logging

from sqlalchemy import text

from aggregate.aggregate import (
    compute_form,
    compute_head_to_head,
    compute_surface_stats,
)
from aggregate.elo import update_elo
from db.db_connection import engine
from ingestion.sackmann import load_from_csv
from logging_config import setup_logging
from transform.transform import transform_raw_matches

logger = logging.getLogger(__name__)


def create_tables(conn):
    logger.info("Creating tables")
    with open("schema.sql") as f:
        conn.execute(text(f.read()))
        conn.commit()


if __name__ == "__main__":
    setup_logging()
    logger.info("Starting seeding process")
    with engine.connect() as conn:
        create_tables(conn)
        load_from_csv(conn)
    transform_raw_matches(sackmann_only=True)
    compute_surface_stats()
    compute_head_to_head()
    compute_form()
    update_elo()
    logger.info("Seeding complete")
