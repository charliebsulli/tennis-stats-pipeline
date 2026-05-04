{{ config(
    materialized='incremental',
    unique_key='match_id'
) }}

select
  match_id,
  tourney_id                            as tournament_id,
  match_date,
  winner_id,
  loser_id,
  coalesce(score, 'Unknown')            as score,
  coalesce(round, 'Unknown')            as round,
  case round
    when 'Q1'                     then -2
    when 'Qualification Round 1'  then -2
    when 'Q2'                     then -1
    when 'Qualification Round 2'  then -1
    when 'Q3'                     then 0
    when 'Qualification Final'    then 0
    when 'ER'                     then 1
    when 'R128'                   then 1
    when 'Round of 128'           then 1
    when 'R64'                    then 2
    when 'Round of 64'            then 2
    when 'R32'                    then 3
    when 'Round of 32'            then 3
    when 'R16'                    then 4
    when 'RR'                     then 4
    when 'Round of 16'            then 4
    when 'QF'                     then 5
    when 'Quarterfinals'          then 5
    when 'SF'                     then 6
    when 'Semifinals'             then 6
    when 'BR'                     then 6
    when 'F'                      then 7
    when 'Final'                  then 7
    else null
  end                                   as round_int
from {{ ref('stg_matches') }}

{% if is_incremental() %}
  where match_id not in (
    select match_id from {{ this }}
  )
{% endif %}