from datetime import datetime, timezone
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text
from db_connection import engine
# from migrate import run_migrations
# from player_id_helper import seed_player_id_lookup
# from transform import transform_raw_matches

load_dotenv()
dataset_path_str = os.getenv("DATASET_PATH")
if dataset_path_str == None:
    raise Exception("Dataset path not set")
DATASET_PATH = Path(dataset_path_str)


def seed_from_csv(conn):
    cur = conn.cursor()
    row = cur.execute("SELECT 1 FROM raw_matches LIMIT 1").fetchone() # check db is empty
    if not row:
        files = DATASET_PATH.glob("atp_matches_[12q]*.csv") # include tour level, qualies, and challengers
        for csv_file in sorted(files):
            df = pd.read_csv(csv_file)
            df['source'] = 'sackmann'
            df['time_added'] = datetime.now(timezone.utc).isoformat()
            df.to_sql("raw_matches", conn, if_exists="append", index=False)
            print(f"Loaded {csv_file.name} - {len(df)} rows")


if __name__ == "__main__":
    with engine.connect() as conn:
        print("Creating tables...")
        with open("schema.sql") as f:
            conn.execute(text(f.read()))
            conn.commit()
        # print("Seeding raw match data from CSV files...")
        # seed_from_csv(conn)
        # conn.commit()
        # conn.close()
        # print("Transforming raw match data...")
        # transform_raw_matches(sackmann_only=True)
        # print("Seeding player ID lookup table...")
        # seed_player_id_lookup()
        # print("Process complete.")
