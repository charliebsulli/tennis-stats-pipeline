import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Connection, text

logger = logging.getLogger(__name__)


load_dotenv()
dataset_path_str = os.getenv("DATASET_PATH")
if dataset_path_str is None:
    raise Exception("Dataset path not set")
DATASET_PATH = Path(dataset_path_str)


def load_from_csv(conn: Connection):
    row = conn.execute(
        text("SELECT 1 FROM raw_matches LIMIT 1")
    ).fetchone()  # check db is empty
    if not row:
        logger.info("Seeding raw match data from CSV files")
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
    else:
        logger.warning("Cannot load CSV data unless raw_matches table is empty")
