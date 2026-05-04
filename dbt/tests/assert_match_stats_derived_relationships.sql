with stats as (
    select * from {{ ref('match_stats') }}
)

select
    p.match_id,
    p.player_id
from stats p
join stats o 
    on p.match_id = o.match_id 
    and p.opponent_id = o.player_id
where 
    -- only check if stats are complete to avoid null comparison issues
    p.complete_stats = true and o.complete_stats = true and (
        p.first_serve_return_points_won != (o.first_serves_in - o.first_serve_points_won) or
        p.second_serve_return_points_won != ((o.service_points - o.first_serves_in) - o.second_serve_points_won) or
        p.break_points_converted != (o.break_points_faced - o.break_points_saved) or
        p.return_points != o.service_points or
        p.first_serve_return_points != o.first_serves_in or
        p.return_games != o.service_games or
        p.break_points_chances != o.break_points_faced
    )
