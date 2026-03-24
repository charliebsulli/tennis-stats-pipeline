import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Connection, text

from aggregate import compute_player_surface_stats
from db_connection import engine
from logging_config import setup_logging
from player_id_helper import seed_player_id_lookup
from transform import transform_raw_matches

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()
dataset_path_str = os.getenv("DATASET_PATH")
if dataset_path_str == None:
    raise Exception("Dataset path not set")
DATASET_PATH = Path(dataset_path_str)


def seed_from_csv(conn: Connection):
    row = conn.execute(
        text("SELECT 1 FROM raw_matches LIMIT 1")
    ).fetchone()  # check db is empty
    if not row:
        files = DATASET_PATH.glob(
            "atp_matches_[12q]*.csv"
        )  # include tour level, qualies, and challengers
        for csv_file in sorted(files):
            df = pd.read_csv(csv_file)
            df["tourney_date"] = df["tourney_date"].map(
                lambda x: date.strptime(str(x), "%Y%m%d")
            )
            df["source"] = "sackmann"
            df["time_added"] = datetime.now(timezone.utc).isoformat()
            df.columns = df.columns.str.lower()
            df.to_sql("raw_matches", conn, if_exists="append", index=False)
            conn.commit()
            logger.info(f"Loaded {csv_file.name} - {len(df)} rows")


if __name__ == "__main__":
    with engine.connect() as conn:
        logger.info("Creating tables...")
        with open("schema.sql") as f:
            conn.execute(text(f.read()))
            conn.commit()
        logger.info("Seeding raw match data from CSV files...")
        seed_from_csv(conn)
    logger.info("Transforming raw match data...")
    transform_raw_matches(sackmann_only=True)
    logger.info("Seeding player ID lookup table...")
    seed_player_id_lookup()
    logger.info("Computing advanced statistics...")
    compute_player_surface_stats()
    logger.info("Process complete.")
