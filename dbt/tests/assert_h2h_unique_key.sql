select
    player_id,
    opponent_id,
    surface,
    count(*) as occurrences
from {{ ref('head_to_head') }}
group by 1, 2, 3
having count(*) > 1
