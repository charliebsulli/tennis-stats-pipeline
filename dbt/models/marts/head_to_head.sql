{{ config(
    materialized='incremental',
    unique_key=['player_id', 'opponent_id', 'surface']
) }}

with affected_players as (
    select distinct 
        ms.player_id
    from {{ ref('match_stats') }} ms
    join {{ ref('stg_matches') }} stg on ms.match_id = stg.match_id
    
    {% if is_incremental() %}
    where stg.time_added > (select max(last_updated) from {{ this }})
    {% endif %}
),

full_history_for_affected as (
    select
        ms.player_id,
        ms.opponent_id,
        t.surface,
        ms.won
    from {{ ref('match_stats') }} ms
    join {{ ref('matches') }} m on ms.match_id = m.match_id
    join {{ ref('tournaments') }} t on m.tournament_id = t.tournament_id
    where ms.player_id in (select player_id from affected_players)
),

surface_h2h as (
    select
        player_id,
        opponent_id,
        surface,
        count(*) filter (where won) as wins,
        count(*) as matches_played
    from full_history_for_affected
    where surface in ('Clay', 'Grass', 'Hard')
    group by 1, 2, 3
),

all_h2h as (
    select
        player_id,
        opponent_id,
        'ALL' as surface,
        count(*) filter (where won) as wins,
        count(*) as matches_played
    from full_history_for_affected
    group by 1, 2, 3
),

unioned as (
    select * from surface_h2h
    union all
    select * from all_h2h
)

select
    player_id,
    opponent_id,
    surface,
    wins,
    matches_played - wins as losses,
    matches_played,
    current_timestamp as last_updated
from unioned
