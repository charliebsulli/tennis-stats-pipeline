select
    match_id,
    player_id,
    count(*) as occurrences
from {{ ref('match_stats') }}
group by 1, 2
having count(*) > 1
