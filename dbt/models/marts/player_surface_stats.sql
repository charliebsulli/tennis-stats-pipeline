{{ config(
    materialized='incremental',
    unique_key=['player_id', 'surface', 'season']
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
        t.surface,
        extract(year from m.match_date)::integer as match_year,
        ms.won,
        ms.aces,
        ms.double_faults,
        ms.service_points,
        ms.first_serves_in,
        ms.first_serve_points_won,
        ms.second_serve_points_won,
        ms.service_games,
        ms.break_points_saved,
        ms.break_points_faced,
        ms.return_points,
        ms.first_serve_return_points,
        ms.first_serve_return_points_won,
        ms.second_serve_return_points_won,
        ms.return_games,
        ms.break_points_converted,
        ms.break_points_chances
    from {{ ref('match_stats') }} ms
    join {{ ref('matches') }} m on ms.match_id = m.match_id
    join {{ ref('tournaments') }} t on m.tournament_id = t.tournament_id
    where ms.player_id in (select player_id from affected_players)
      and ms.complete_stats = true
),

-- Aggregate by surface and season (including career season=0)
surface_stats as (
    select
        player_id,
        surface,
        coalesce(match_year, 0) as season,
        count(*) as matches_played,
        count(*) filter (where won) as won,
        sum(aces) as aces,
        sum(double_faults) as double_faults,
        sum(service_points) as service_points,
        sum(first_serves_in) as first_serves_in,
        sum(first_serve_points_won) as first_serve_points_won,
        sum(second_serve_points_won) as second_serve_points_won,
        sum(service_games) as service_games,
        sum(break_points_saved) as break_points_saved,
        sum(break_points_faced) as break_points_faced,
        sum(return_points) as return_points,
        sum(first_serve_return_points) as first_serve_return_points,
        sum(first_serve_return_points_won) as first_serve_return_points_won,
        sum(second_serve_return_points_won) as second_serve_return_points_won,
        sum(return_games) as return_games,
        sum(break_points_converted) as break_points_converted,
        sum(break_points_chances) as break_points_chances
    from full_history_for_affected
    where surface in ('Clay', 'Grass', 'Hard')
    group by grouping sets (
        (player_id, surface, match_year),
        (player_id, surface)
    )
),

-- Aggregate by 'ALL' surface for both season and career
all_surface_stats as (
    select
        player_id,
        'ALL' as surface,
        coalesce(match_year, 0) as season,
        count(*) as matches_played,
        count(*) filter (where won) as won,
        sum(aces) as aces,
        sum(double_faults) as double_faults,
        sum(service_points) as service_points,
        sum(first_serves_in) as first_serves_in,
        sum(first_serve_points_won) as first_serve_points_won,
        sum(second_serve_points_won) as second_serve_points_won,
        sum(service_games) as service_games,
        sum(break_points_saved) as break_points_saved,
        sum(break_points_faced) as break_points_faced,
        sum(return_points) as return_points,
        sum(first_serve_return_points) as first_serve_return_points,
        sum(first_serve_return_points_won) as first_serve_return_points_won,
        sum(second_serve_return_points_won) as second_serve_return_points_won,
        sum(return_games) as return_games,
        sum(break_points_converted) as break_points_converted,
        sum(break_points_chances) as break_points_chances
    from full_history_for_affected
    group by grouping sets (
        (player_id, match_year),
        (player_id)
    )
),

unioned as (
    select * from surface_stats
    union all
    select * from all_surface_stats
)

select
    current_timestamp as last_updated,
    player_id,
    surface,
    season,
    matches_played,
    won,
    aces,
    double_faults,
    service_points,
    first_serves_in,
    first_serve_points_won,
    second_serve_points_won,
    service_games,
    break_points_saved,
    break_points_faced,
    return_points,
    first_serve_return_points,
    first_serve_return_points_won,
    second_serve_return_points_won,
    return_games,
    break_points_converted,
    break_points_chances,
    service_points - first_serves_in as second_serve_points,
    (service_games - (break_points_faced - break_points_saved)) as service_games_won,
    return_points - first_serve_return_points as second_serve_return_points
from unioned
