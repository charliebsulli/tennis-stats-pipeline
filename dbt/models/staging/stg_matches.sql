{{ config(
    materialized='incremental',
    unique_key='match_id'
) }}

with joined as (
  select
    coalesce(r.winner_id, wl.player_id) as winner_id,
    coalesce(r.loser_id, ll.player_id) as loser_id,
    coalesce(r.tourney_id, r.rapidapi_tournament_id::text) as tourney_id,
    coalesce(r.tourney_date, r.match_date) as match_date,
    case 
      when r.surface = 'Hardcourt indoor' then 'Hard'
      when r.surface = 'Hardcourt outdoor' then 'Hard'
      when r.surface = 'Red clay' then 'Clay'
      when r.surface = 'Red clay indoor' then 'Clay'
      when r.surface is null then 'Unknown'
      else r.surface
    end as surface,
    r.time_added,
    r.source,
    r.match_id,
    r.tourney_name,
    r.draw_size,
    r.tourney_level,
    r.match_num,
    r.winner_seed,
    r.winner_entry,
    r.winner_name,
    r.winner_hand,
    r.winner_ht,
    r.winner_ioc,
    r.winner_age,
    r.loser_seed,
    r.loser_entry,
    r.loser_name,
    r.loser_hand,
    r.loser_ht,
    r.loser_ioc,
    r.loser_age,
    r.score,
    r.best_of,
    r.round,
    r.minutes,
    r.w_ace,
    r.w_df,
    r.w_svpt,
    r.w_1stIn,
    r.w_1stWon,
    r.w_2ndWon,
    r.w_SvGms,
    r.w_bpSaved,
    r.w_bpFaced,
    r.l_ace,
    r.l_df,
    r.l_svpt,
    r.l_1stIn,
    r.l_1stWon,
    r.l_2ndWon,
    r.l_SvGms,
    r.l_bpSaved,
    r.l_bpFaced,
    r.winner_rank,
    r.winner_rank_points,
    r.loser_rank,
    r.loser_rank_points,
    r.rapidapi_match_id,
    r.rapidapi_tournament_id,
    r.rapidapi_winner_id,
    r.rapidapi_loser_id
  from {{ source('raw', 'raw_matches') }} as r
  left join {{ source('raw', 'player_id_lookup') }} as wl on r.rapidapi_winner_id = wl.api_player_id
  left join {{ source('raw', 'player_id_lookup') }} as ll on r.rapidapi_loser_id = ll.api_player_id

  {% if is_incremental() %}
    where r.match_id not in (select match_id from {{ this }})
  {% endif %}
)

select *
from joined
where winner_id != loser_id
