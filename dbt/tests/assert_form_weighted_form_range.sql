select
    player_id,
    surface,
    weighted_form
from {{ ref('form') }}
where weighted_form < 0 or weighted_form > 1
