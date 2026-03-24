CREATE TABLE head_to_head (
    player_id       INTEGER REFERENCES players(player_id),
    opponent_id     INTEGER REFERENCES players(player_id),
    surface         TEXT,
    wins            INTEGER NOT NULL,
    losses          INTEGER NOT NULL,
    matches_played  INTEGER NOT NULL,
    last_updated    TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (player_id, opponent_id, surface)
);