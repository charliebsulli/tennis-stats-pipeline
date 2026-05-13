select
    player_id,
    surface,
    count(*) as occurrences
from {{ ref('form') }}
group by 1, 2
having count(*) > 1
