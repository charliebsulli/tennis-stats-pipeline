select *
from {{ ref('head_to_head') }}
where 
    wins < 0 or
    losses < 0 or
    matches_played < 0 or
    wins + losses != matches_played
