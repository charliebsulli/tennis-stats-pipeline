select
    player_id,
    surface,
    season,
    count(*) as occurrences
from {{ ref('player_surface_stats') }}
group by 1, 2, 3
having count(*) > 1
