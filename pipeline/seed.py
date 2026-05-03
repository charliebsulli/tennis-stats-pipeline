import logging

from sqlalchemy import text

from pipeline.aggregate.elo import update_elo
from pipeline.aggregate.form import compute_form
from pipeline.aggregate.head_to_head import compute_head_to_head
from pipeline.aggregate.surface_stats import compute_surface_stats
from pipeline.db.db_connection import engine
from pipeline.ingestion.sackmann import load_from_csv
from pipeline.logging_config import setup_logging
from pipeline.transform.player_id_helper import seed_players
from pipeline.transform.transform import transform_raw_matches

logger = logging.getLogger(__name__)


def create_tables(conn):
    logger.info("Creating tables")
    with open("pipeline/schema.sql") as f:
        conn.execute(text(f.read()))
        conn.commit()


if __name__ == "__main__":
    setup_logging()
    logger.info("Starting seeding process")
    with engine.connect() as conn:
        create_tables(conn)
        load_from_csv(conn)
        seed_players(conn)
    # transform_raw_matches(sackmann_only=True)
    # compute_surface_stats()
    # compute_head_to_head()
    # compute_form()
    # update_elo()
    logger.info("Seeding complete")
