CREATE TABLE players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT, -- the sackmann dataset already establishes as id so we use that for all players
    name TEXT NOT NULL,
    nationality TEXT,
    hand TEXT,
    dob TEXT
);

CREATE TABLE tournaments (
    tournament_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    surface TEXT NOT NULL,
    tournament_level TEXT NOT NULL
);

-- will have to decide whether each year of an event counts as a separate tournament or same

CREATE TABLE matches (
    match_id INTEGER PRIMARY KEY,
    tournament_id TEXT REFERENCES tournaments(tournament_id),
    match_date DATE NOT NULL,
    round TEXT NOT NULL,
    winner_id INTEGER REFERENCES players(player_id),
    loser_id INTEGER REFERENCES players(player_id),
    score TEXT
);
