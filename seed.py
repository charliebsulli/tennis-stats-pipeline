from datetime import datetime, timezone
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from db_connection import get_connection

# load match data from the Sackmann dataset .csvs into the raw_matches table
if __name__ == "__main__":
    load_dotenv()
    dataset_path_str = os.getenv("DATASET_PATH")
    if dataset_path_str == None:
        raise Exception("Dataset path not set")
    dataset_path = Path(dataset_path_str)
    
    conn = get_connection()
    cur = conn.cursor()

    with open("schema.sql") as f:
        cur.executescript(f.read())

    # load matches
    files = dataset_path.glob("atp_matches_[12q]*.csv") # include tour level, qualies, and challengers
    for csv_file in sorted(files):
        df = pd.read_csv(csv_file)
        df['source'] = 'sackmann'
        df['time_added'] = datetime.now(timezone.utc).isoformat()
        df.to_sql("raw_matches", conn, if_exists="append", index=False)
        print(f"Loaded {csv_file.name} - {len(df)} rows")

    conn.close()