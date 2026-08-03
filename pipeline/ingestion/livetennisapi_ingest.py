import logging
import re
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from pipeline.db.db_connection import engine
from pipeline.ingestion.ingest import make_insert_or_ignore
from pipeline.ingestion.livetennisapi_api_calls import is_enabled, iter_history_matches

logger = logging.getLogger(__name__)

SOURCE = "livetennisapi"

# The provider reports lowercase surfaces; the warehouse uses title case.
SURFACE_NAMES = {"hard": "Hard", "clay": "Clay", "grass": "Grass"}

BEST_OF = {"BO3": 3, "BO5": 5}

IOC_PATTERN = re.compile(r"^[A-Z]{3}$")


def ingest_history(from_date, to_date):
    """
    Ingest completed matches from Live Tennis API for a date window.

    Optional: does nothing unless LIVETENNISAPI_KEY is set.
    """
    if not is_enabled():
        logger.info("LIVETENNISAPI_KEY not set, skipping %s ingestion", SOURCE)
        return

    df = build_history_df(from_date, to_date)
    if df.empty:
        logger.info("No %s data found for %s..%s", SOURCE, from_date, to_date)
        return

    df = drop_matches_already_ingested(df)
    if df.empty:
        logger.info("All %s matches for %s..%s were already ingested", SOURCE, from_date, to_date)
        return

    df["source"] = SOURCE
    df["time_added"] = datetime.now(timezone.utc).isoformat()
    df.columns = df.columns.str.lower()

    logger.info("Attempting to insert %s matches from %s", len(df), SOURCE)

    with engine.connect() as conn:
        rows = df.to_sql(
            "raw_matches",
            conn,
            if_exists="append",
            index=False,
            method=make_insert_or_ignore("ltapi_match_id"),
        )
        logger.info("Inserted %s matches from %s", rows, SOURCE)


def build_history_df(from_date, to_date):
    rows = []
    for match in iter_history_matches(from_date, to_date):
        row = extract_match(match)
        if row:
            rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).drop_duplicates("ltapi_match_id")


def extract_match(match):
    """
    Map one provider match onto the raw_matches columns we can fill honestly.

    Fields the provider does not carry are simply absent, so they stay NULL:
    draw_size, tourney_level, match_num, seeds, entry, height, minutes and
    every serve/return stat column. Rows therefore land with
    complete_stats = false and are excluded from the serve/return
    aggregations by the existing filters, while still counting for Elo,
    head-to-head and form.
    """
    if match.get("status") != "completed":
        return {}

    if match.get("is_doubles"):
        return {}

    winner = match.get("winner")
    if winner not in (1, 2):
        # Without a derived winner the row cannot be oriented.
        return {}

    players = match.get("players") or {}
    winner_player = players.get(f"p{winner}") or {}
    loser_player = players.get("p2" if winner == 1 else "p1") or {}

    if not winner_player.get("name") or not loser_player.get("name"):
        return {}

    match_date = parse_match_date(match.get("scheduled_time"))
    if match_date is None:
        return {}

    tourney_name = match.get("tournament")

    return {
        "ltapi_match_id": match.get("id"),
        "ltapi_winner_id": winner_player.get("id"),
        "ltapi_loser_id": loser_player.get("id"),
        "tourney_id": build_tourney_id(tourney_name),
        "tourney_name": tourney_name,
        "surface": SURFACE_NAMES.get(match.get("surface")),
        "tourney_date": match_date,
        "match_date": match_date,
        "round": match.get("round"),
        "best_of": BEST_OF.get(match.get("format")),
        "winner_name": winner_player.get("name"),
        "winner_hand": winner_player.get("hand"),
        "winner_ioc": clean_ioc(winner_player.get("country")),
        "winner_rank": winner_player.get("ranking"),
        "winner_rank_points": winner_player.get("ranking_points"),
        "loser_name": loser_player.get("name"),
        "loser_hand": loser_player.get("hand"),
        "loser_ioc": clean_ioc(loser_player.get("country")),
        "loser_rank": loser_player.get("ranking"),
        "loser_rank_points": loser_player.get("ranking_points"),
        "score": compute_score(match.get("score"), winner),
    }


def parse_match_date(scheduled_time):
    if not scheduled_time:
        return None
    try:
        return datetime.fromisoformat(scheduled_time.replace("Z", "+00:00")).date()
    except (AttributeError, ValueError):
        logger.warning("Could not parse scheduled_time %r", scheduled_time)
        return None


def build_tourney_id(tourney_name):
    """
    Derive a tournament key from the name.

    The provider exposes `tournament` as free text and has no tournament id,
    so this is explicitly a name-derived key, namespaced to keep it from
    colliding with Sackmann ids or RapidAPI season ids.
    """
    if not tourney_name:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", tourney_name.lower()).strip("-")
    return f"ltapi:{slug}" if slug else None


def clean_ioc(country):
    """
    Only accept a country that already looks like a 3-letter IOC code.

    The provider does not document the format of `country`, so anything that
    is not obviously an IOC code is dropped rather than written into a column
    the rest of the pipeline reads as one.
    """
    if isinstance(country, str) and IOC_PATTERN.match(country):
        return country
    return None


def compute_score(score, winner):
    """
    Build "6-4 3-6 7-5" from the per-set games, oriented winner first.

    The provider documents that a completed match observed live can carry an
    empty games array, so anything not well formed returns None and the score
    stays NULL rather than being guessed at.
    """
    if not isinstance(score, dict):
        return None

    games = score.get("games")
    if not isinstance(games, list) or len(games) != 2:
        return None

    p1_games, p2_games = games
    if not isinstance(p1_games, list) or not isinstance(p2_games, list):
        return None
    if not p1_games or len(p1_games) != len(p2_games):
        return None
    if not all(isinstance(g, int) for g in p1_games + p2_games):
        return None

    if winner == 1:
        pairs = zip(p1_games, p2_games)
    else:
        pairs = zip(p2_games, p1_games)

    return " ".join(f"{a}-{b}" for a, b in pairs)


def drop_matches_already_ingested(df):
    """
    Drop matches another source already ingested.

    raw_matches is deduplicated per provider id, so without this the same
    real-world match arriving from two providers would become two rows and be
    counted twice by Elo, head-to-head and form.
    """
    if df.empty:
        return df

    with engine.connect() as conn:
        existing = pd.read_sql(
            text(
                """
                SELECT winner_name, loser_name, match_date
                FROM raw_matches
                WHERE match_date = ANY(:match_dates)
                """
            ),
            conn,
            params={"match_dates": list(df["match_date"].unique())},
        )

    if existing.empty:
        return df

    seen = {
        (normalize_key(row.winner_name), normalize_key(row.loser_name), row.match_date)
        for row in existing.itertuples()
    }

    keep = [
        (
            normalize_key(row.winner_name),
            normalize_key(row.loser_name),
            row.match_date,
        )
        not in seen
        for row in df.itertuples()
    ]

    dropped = len(df) - sum(keep)
    if dropped:
        logger.info("Skipping %s matches already ingested from another source", dropped)

    return df[keep]


def normalize_key(name):
    if not isinstance(name, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "", name.lower())
