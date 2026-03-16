import os
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

dataset_path_str = os.getenv("DATASET_PATH")
if dataset_path_str == None:
    raise Exception("Dataset path not set")

DATASET = Path(dataset_path_str)
con = sqlite3.connect("tennis.db")
cur = con.cursor()

# with open("schema.sql") as f:
#     cur.executescript(f.read())

# load players first
df = pd.read_csv(DATASET / "atp_players.csv")
df.to_sql("players", con, if_exists="append", index=False)

columns = [
    "tourney_name",
    "surface",
    "tourney_date", # might need more specific dates
    "winner_id", # should probably use my own id to make it universal
    "loser_id",
    "winner_name",
    "loser_name",
    "score",
    "round"
]

# load matches
all_match_files = DATASET.glob("atp_matches_*.csv")
files = [f for f in all_match_files if ("doubles" not in f.name and "amateur" not in f.name)]
for csv_file in sorted(files):
    df = pd.read_csv(csv_file)
    df = df[columns]
    df.to_sql("matches", con, if_exists="append", index=False)
    print(f"Loaded {csv_file.name} - {len(df)} rows")

con.close()