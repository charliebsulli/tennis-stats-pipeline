select 1
from {{ ref('match_stats') }}
where break_points_converted < 0