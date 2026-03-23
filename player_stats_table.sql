CREATE TABLE player_surface_stats (
    last_updated TIMESTAMPTZ NOT NULL,

    player_id INTEGER REFERENCES players(player_id),
    surface TEXT, -- NULL for all surfaces
    season INTEGER, -- year, NULL for career

    matches_played INTEGER,
    won INTEGER,

    aces INTEGER,
    double_faults INTEGER,
    service_points INTEGER,
    first_serves_in INTEGER,
    first_serve_points_won INTEGER,
    second_serve_points_won INTEGER,
    second_serve_points INTEGER, -- service_points - first_serves_in
    service_games INTEGER,
    service_games_won INTEGER, -- (service_games - (break_points_faced - break_points_saved))
    break_points_saved INTEGER,
    break_points_faced INTEGER,

    return_points INTEGER,
    first_serve_return_points INTEGER,
    first_serve_return_points_won INTEGER,
    second_serve_return_points INTEGER, -- return_points - first_serve_return_points
    second_serve_return_points_won INTEGER,
    return_games INTEGER,
    break_points_converted INTEGER, -- every break point converted is a return game won
    break_points_chances INTEGER,

    primary key (player_id, surface, season)
)