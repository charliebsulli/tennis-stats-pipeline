import json
import unicodedata
from sqlalchemy import text
from api_calls import get_rankings
from db_connection import engine
from rapidfuzz import process, fuzz
import logging

logger = logging.getLogger(__name__)

def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = name.replace('-', ' ')
    return name

def fuzzy_match_player(api_player_id, api_name, conn):
    rows = conn.execute(text("SELECT player_id, name FROM players")).fetchall()
    names = {normalize_name(row.name): row.player_id for row in rows}

    if not names:
        raise ValueError("No players in database to match against, populate players by transforming seed data first")

    match, confidence, _ = process.extractOne(
        normalize_name(api_name), names.keys(), scorer=fuzz.token_sort_ratio
    )

    if confidence >= 90:
        conn.execute(text("""
            INSERT INTO player_id_lookup (player_id, api_player_id, api_name, match_type, confidence)
            VALUES (:player_id, :api_player_id, :api_name, :match_type, :confidence)
        """), {
            "player_id": names[match],
            "api_player_id": api_player_id,
            "api_name": api_name,
            "match_type": "auto",
            "confidence": confidence
        })
        return names[match]
    else:
        return None

def translate_player_id(api_player_id, conn):
    result = conn.execute(text("""
        SELECT player_id FROM player_id_lookup WHERE api_player_id = :api_player_id
    """), {"api_player_id": api_player_id}).fetchone()
    return result.player_id if result else None

def generate_player_id(api_player_id, api_name, conn):
    result = conn.execute(text("""
        INSERT INTO players (name) VALUES (:name) RETURNING player_id
    """), {"name": api_name}).fetchone()
    player_id = result.player_id

    conn.execute(text("""
        INSERT INTO player_id_lookup (player_id, api_player_id, api_name, match_type, confidence)
        VALUES (:player_id, :api_player_id, :api_name, :match_type, :confidence)
    """), {
        "player_id": player_id,
        "api_player_id": api_player_id,
        "api_name": api_name,
        "match_type": "new",
        "confidence": -1
    })
    return player_id

def seed_player_id_lookup():
    response = get_rankings()
    if response is None:
        logger.warning("Failed to fetch rankings. Skipping player_id lookup table seeding...")
        return
    try:
        response_json = response.json()
    except json.JSONDecodeError as e:
        logger.exception(f"Failed to decode JSON response")
        logger.warning("Skipping player_id lookup table seeding...")
        return
    try:
        name_id_pairs = [(p["team"]["name"], p["team"]["id"]) for p in response_json["rankings"]]
    except KeyError:
        logger.exception("Unexpected format of JSON. Skipping player_id lookup table seeding...")
        return

    with engine.begin() as conn:
        for name, api_id in name_id_pairs:
            player_id = fuzzy_match_player(api_id, name, conn)
            if player_id is None:
                generate_player_id(api_id, name, conn)

def get_player_id(api_player_id, api_name, conn):
    player_id = translate_player_id(api_player_id, conn)
    if player_id is not None:
        return player_id
    player_id = fuzzy_match_player(api_player_id, api_name, conn)
    if player_id is not None:
        return player_id
    return generate_player_id(api_player_id, api_name, conn)

if __name__ == "__main__":
    seed_player_id_lookup()