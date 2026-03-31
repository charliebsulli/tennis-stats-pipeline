CREATE TABLE averaged_surface_elo_history (
    player_id INTEGER NOT NULL REFERENCES players(player_id),
    match_id INTEGER NOT NULL REFERENCES matches(match_id),
    surface TEXT NOT NULL,
    match_date DATE NOT NULL,

    expected REAL NOT NULL,
    won BOOLEAN NOT NULL,
    averaged_surface_elo REAL NOT NULL,

    overall_surface TEXT NOT NULL DEFAULT 'ALL' CHECK (overall_surface = 'ALL'),

    -- surface-specific elo_history row (same player/match/surface)
    FOREIGN KEY (player_id, match_id, surface)
        REFERENCES elo_history(player_id, match_id, surface),

    -- overall elo_history row (same player/match, but surface='ALL')
    FOREIGN KEY (player_id, match_id, overall_surface)
        REFERENCES elo_history(player_id, match_id, surface),

    PRIMARY KEY (player_id, match_id, surface)
);
