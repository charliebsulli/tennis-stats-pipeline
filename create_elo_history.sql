CREATE TABLE elo_history (
    player_id       INTEGER REFERENCES players(player_id),
    match_id        INTEGER REFERENCES matches(match_id),
    surface         TEXT NOT NULL,      -- 'Hard', 'Clay', 'Grass', 'ALL'
    match_date      DATE NOT NULL,
    elo_before      REAL NOT NULL,
    elo_after       REAL NOT NULL,
    k_factor        REAL NOT NULL,      -- store what K was used, useful for auditing
    opponent_id     INTEGER REFERENCES players(player_id),
    opponent_elo    REAL NOT NULL,      -- opponent rating at time of match
    expected        REAL NOT NULL,      -- E(A) — useful for validation later
    won             BOOLEAN NOT NULL,
    PRIMARY KEY (player_id, match_id, surface)
);