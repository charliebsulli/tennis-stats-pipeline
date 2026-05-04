{{ config(
    materialized='incremental',
    unique_key=['match_id', 'player_id']
) }}

with winner_stats as (
  select
    match_id,
    winner_id                                     as player_id,
    loser_id                                      as opponent_id,
    true                                          as won,
    w_ace                                         as aces,
    w_df                                          as double_faults,
    w_svpt                                        as service_points,
    w_1stIn                                       as first_serves_in,
    w_1stWon                                      as first_serve_points_won,
    w_2ndWon                                      as second_serve_points_won,
    w_SvGms                                       as service_games,
    w_bpSaved                                     as break_points_saved,
    w_bpFaced                                     as break_points_faced,
    l_svpt                                        as return_points,
    l_1stIn                                       as first_serve_return_points,
    l_1stIn - l_1stWon                            as first_serve_return_points_won,
    l_svpt - l_1stIn - l_2ndWon                   as second_serve_return_points_won,
    l_SvGms                                       as return_games,
    l_bpFaced - l_bpSaved                         as break_points_converted,
    l_bpFaced                                     as break_points_chances
  from {{ ref('stg_matches') }}
),

loser_stats as (
  select
    match_id,
    loser_id                                      as player_id,
    winner_id                                     as opponent_id,
    false                                         as won,
    l_ace                                         as aces,
    l_df                                          as double_faults,
    l_svpt                                        as service_points,
    l_1stIn                                       as first_serves_in,
    l_1stWon                                      as first_serve_points_won,
    l_2ndWon                                      as second_serve_points_won,
    l_SvGms                                       as service_games,
    l_bpSaved                                     as break_points_saved,
    l_bpFaced                                     as break_points_faced,
    w_svpt                                        as return_points,
    w_1stIn                                       as first_serve_return_points,
    w_1stIn - w_1stWon                            as first_serve_return_points_won,
    w_svpt - w_1stIn - w_2ndWon                   as second_serve_return_points_won,
    w_SvGms                                       as return_games,
    w_bpFaced - w_bpSaved                         as break_points_converted,
    w_bpFaced                                     as break_points_chances
  from {{ ref('stg_matches') }}
),

unioned as (
  select * from winner_stats
  union all
  select * from loser_stats
)

select
  *,
  (
    aces                            is not null and
    double_faults                   is not null and
    service_points                  is not null and
    first_serves_in                 is not null and
    first_serve_points_won          is not null and
    second_serve_points_won         is not null and
    service_games                   is not null and
    break_points_saved              is not null and
    break_points_faced              is not null and
    return_points                   is not null and
    first_serve_return_points       is not null and
    first_serve_return_points_won   is not null and
    second_serve_return_points_won  is not null and
    return_games                    is not null and
    break_points_converted          is not null and
    break_points_chances            is not null
  )                                               as complete_stats
from unioned

{% if is_incremental() %}
  where match_id not in (
    select match_id from {{ this }}
  )
{% endif %}