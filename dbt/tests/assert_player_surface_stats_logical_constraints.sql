select *
from {{ ref('player_surface_stats') }}
where 
    matches_played < 0 or
    won < 0 or
    won > matches_played or
    aces < 0 or
    double_faults < 0 or
    service_points < 0 or
    first_serves_in < 0 or
    first_serves_in > service_points or
    first_serve_points_won < 0 or
    first_serve_points_won > first_serves_in or
    second_serve_points_won < 0 or
    second_serve_points_won > (service_points - first_serves_in) or
    service_games < 0 or
    break_points_saved < 0 or
    break_points_faced < 0 or
    break_points_saved > break_points_faced or
    return_points < 0 or
    first_serve_return_points < 0 or
    first_serve_return_points_won < 0 or
    second_serve_return_points_won < 0 or
    return_games < 0 or
    break_points_converted < 0 or
    break_points_chances < 0 or
    break_points_converted > break_points_chances
