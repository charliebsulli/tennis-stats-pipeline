import logging
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import text

from db.db_connection import engine

logger = logging.getLogger(__name__)


def compute_form():
    logger.info("Updating player form")
    with engine.connect() as conn:
        with open("queries/recent_matches.sql") as f:
            query = text(f.read())
        df = pd.read_sql(query, conn)

    grouped = df.groupby(["player_id", "surface"])
    output = []
    for (player_id, surface), group in grouped:
        output.append(
            {
                "matches_total": len(group),
                "won": sum(group["won"]),
                "player_id": player_id,
                "surface": surface,
                "last_updated": datetime.now(timezone.utc),
                "weighted_form": find_weighted_form(group, 0.97),
            }
        )
    result = pd.DataFrame(output)
    with engine.begin() as conn:
        result.to_sql("player_form", conn, if_exists="delete_rows", index=False)
    logger.info("Updated player form")


def find_weighted_form(df: pd.DataFrame, alpha: float):
    if len(df) < 5:
        logger.debug(
            f"Skipping player form for player with {len(df)} matches in last 90 days"
        )
        return None
    score, total = 0, 0
    now = date.today()
    df["days_ago"] = (now - df["match_date"]).dt.days
    df["weight"] = alpha ** df["days_ago"]
    score = (df["won"] * df["weight"]).sum()
    total = df["weight"].sum()
    # for index, row in df.iterrows():
    #     days_ago = (now - row["match_date"]).days
    #     weight = alpha**days_ago
    #     total += weight
    #     if row["won"]:
    #         score += weight
    if total == 0:
        logger.warning("Total score for form computation is 0")
        return None
    return score / total
