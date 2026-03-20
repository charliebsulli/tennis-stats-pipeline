import unicodedata

from api_calls import get_rankings
from db_connection import get_connection
from rapidfuzz import process, fuzz


# I noticed 3 problems causing low confidence matches
# when players were clearly the same: capitalization, hyphens, accents
def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = unicodedata.normalize('NFD', name) # decomposes unicode
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn') # removes the accents
    name = name.replace('-', ' ')
    return name


def fuzzy_match_player(api_player_id, api_name, conn):
    curr = conn.cursor()
    names = {normalize_name(row[1]): row[0] for row in curr.execute("SELECT player_id, name FROM players")}
    if not names:
        raise ValueError("No players in database to match against, populate players by transforming seed data first")
    match, confidence, _ = process.extractOne(normalize_name(api_name), names.keys(), scorer=fuzz.token_sort_ratio)
    if confidence >= 90:
        curr.execute("INSERT INTO player_id_lookup (player_id, api_player_id, api_name, match_type, confidence) VALUES (?, ?, ?, ?, ?)", (names[match], api_player_id, api_name, "auto", confidence))
        conn.commit()
        return names[match]
    else:
        return None


def translate_player_id(api_player_id, conn):
    curr = conn.cursor()
    result = curr.execute("SELECT player_id FROM player_id_lookup WHERE api_player_id = ? ", (api_player_id,)).fetchone()
    if result:
        return result[0]
    else:
        return None
    

def generate_player_id(api_player_id, api_name, conn):
    curr = conn.cursor()
    curr.execute("INSERT INTO players (name) VALUES (?)", (api_name,))
    player_id = curr.lastrowid
    conn.commit()
    curr.execute("INSERT INTO player_id_lookup (player_id, api_player_id, api_name, match_type, confidence) VALUES (?, ?, ?, ?, ?)", (player_id, api_player_id, api_name, "new", -1))
    return player_id


def seed_player_id_lookup():
    response = get_rankings().json()
    name_id_pairs = [(p["team"]["name"], p["team"]["id"]) for p in response["rankings"]]

    conn = get_connection()

    for name, id in name_id_pairs:
        player_id = fuzzy_match_player(id, name, conn)
        if player_id is None:
            generate_player_id(id, name, conn)


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