select *
from {{ ref('match_stats') }}
where 
    aces < 0 or
    double_faults < 0 or
    service_points < 0 or
    first_serves_in < 0 or
    first_serve_points_won < 0 or
    second_serve_points_won < 0 or
    service_games < 0 or
    break_points_saved < 0 or
    break_points_faced < 0 or
    return_points < 0 or
    first_serve_return_points < 0 or
    first_serve_return_points_won < 0 or
    second_serve_return_points_won < 0 or
    return_games < 0 or
    break_points_converted < 0 or
    break_points_chances < 0
