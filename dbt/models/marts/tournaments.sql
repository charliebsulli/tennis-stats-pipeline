{{ config(
    materialized='incremental',
    unique_key='tournament_id'
) }}

select distinct on (tournament_id)
  tourney_id                            as tournament_id,
  coalesce(tourney_name, 'Unknown')    as name,
  coalesce(surface, 'Unknown')         as surface,
  coalesce(tourney_level, 'Unknown')   as tournament_level
from {{ ref('stg_matches') }}

{% if is_incremental() %}
  where tourney_id not in (
    select tournament_id from {{ this }}
  )
{% endif %}