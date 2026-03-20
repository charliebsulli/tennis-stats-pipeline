CREATE TABLE player_id_lookup (
    player_id INTEGER REFERENCES players(player_id),
    api_player_id INTEGER NOT NULL,
    api_name TEXT NOT NULL,
    match_type TEXT NOT NULL,
    confidence REAL NOT NULL,

    PRIMARY KEY (player_id, api_player_id)
);