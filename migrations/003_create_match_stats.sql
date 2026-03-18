CREATE TABLE match_stats (
    match_id INTEGER REFERENCES matches(match_id),
    player_id INTEGER REFERENCES players(player_id),
    opponent_id INTEGER REFERENCES players(player_id),
    won BOOLEAN NOT NULL,

    aces INTEGER,
    double_faults INTEGER,
    service_points INTEGER,
    first_serves_in INTEGER,
    first_serve_points_won INTEGER,
    second_serve_points_won INTEGER,
    service_games INTEGER,
    break_points_saved INTEGER,
    break_points_faced INTEGER,

    return_points INTEGER,
    first_serve_return_points INTEGER,
    first_serve_return_points_won INTEGER,
    second_serve_return_points_won INTEGER,
    return_games INTEGER,
    break_points_converted INTEGER,
    break_points_chances INTEGER,

    PRIMARY KEY (match_id, player_id)
)