import pandas as pd
from sqlalchemy import text

from db.db_connection import engine


def evaluate_elo_accuracy(start_date: str, end_date: str, surface: str = "ALL") -> None:
    if surface == "ALL":
        table_name = "elo_history"
    else:
        table_name = "averaged_surface_elo_history"

    with engine.connect() as conn:
        df = pd.read_sql(
            text(f"""
                SELECT DISTINCT ON (match_id)
                    expected,
                    won
                FROM {table_name}
                WHERE surface = :surface
                AND match_date >= :start
                AND match_date < :end
            """),
            conn,
            params={"start": start_date, "end": end_date, "surface": surface},
        )

    if df.empty:
        print(f"No data found for surface={surface} in the given date range")
        return

    df["predicted_win"] = df["expected"] >= 0.5
    df["correct"] = df["predicted_win"] == df["won"]

    total = len(df)
    correct = df["correct"].sum()
    accuracy = correct / total

    print(
        f"Surface: {surface:<6} | Total: {total:<6} | Correct: {correct:<6} | Accuracy: {accuracy:.1%}"
    )


if __name__ == "__main__":
    for surface in ["ALL", "Hard", "Clay", "Grass"]:
        evaluate_elo_accuracy("2023-01-01", "2023-12-25", surface)
