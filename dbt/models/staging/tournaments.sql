select distinct on (tourney_id)
    tourney_id as tournament_id,
    tourney_name as name,
    tourney_level as tournament_level,
    surface
from {{ source('raw', 'raw_matches') }}