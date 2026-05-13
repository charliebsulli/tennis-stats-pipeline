with recent_matches as (
    select
        player_id,
        'ALL' as surface,
        match_date,
        won
    from (
        select
            ms.player_id,
            'ALL' as surface,
            m.match_date,
            ms.won,
            row_number() over (
                partition by ms.player_id
                order by m.match_date desc, m.round_int desc
            ) as rn
        from {{ ref('match_stats') }} as ms
        join {{ ref('matches') }} as m on ms.match_id = m.match_id
        where match_date >= now() - interval '90 days'
    )
    where rn <= 20

    union all

    select
        player_id,
        surface,
        match_date,
        won
    from (
        select
            ms.player_id,
            t.surface,
            m.match_date,
            ms.won,
            row_number() over (
                partition by ms.player_id, t.surface
                order by m.match_date desc, m.round_int desc
            ) as rn
        from {{ ref('match_stats') }} as ms
        join {{ ref('matches') }} as m on ms.match_id = m.match_id
        join {{ ref('tournaments') }} as t on m.tournament_id = t.tournament_id
        where match_date >= now() - interval '90 days'
    )
    where rn <= 20
      and surface in ('Clay', 'Hard', 'Grass')
),

matches_with_weights as (
    select
        recent_matches.*,
        power(0.97, now()::date - match_date) as recency_weight
    from recent_matches
)

select
    player_id,
    surface,
    count(*) as matches_total,
    sum(case when won then 1 else 0 end) as won,
    sum(case when won then recency_weight else 0 end) / sum(recency_weight) as weighted_form,
    now() as last_updated
from matches_with_weights
group by player_id, surface
