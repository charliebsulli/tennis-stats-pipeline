WITH overall_ratings AS (
    SELECT DISTINCT ON (e.player_id)
        e.player_id,
        e.elo_after AS overall_elo
    FROM elo_history AS e
    JOIN matches AS m ON e.match_id = m.match_id
    WHERE e.surface = 'ALL'
    -- AND e.match_date >= NOW() - INTERVAL '1 year'
    ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
),
overall_rankings AS (
    SELECT
        o.player_id,
        o.overall_elo,
        RANK() OVER (ORDER BY o.overall_elo DESC) AS overall_rank
    FROM overall_ratings AS o
),
surface_ratings AS (
    SELECT DISTINCT ON (a.player_id)
        a.player_id,
        a.surface,
        a.averaged_surface_elo AS surface_elo
    FROM averaged_surface_elo_history AS a
    JOIN matches AS m ON a.match_id = m.match_id
    WHERE a.surface = 'Hard' -- Change this to compare a different surface
    -- AND a.match_date >= NOW() - INTERVAL '1 year'
    ORDER BY a.player_id, a.match_date DESC, m.round_int DESC
),
surface_rankings AS (
    SELECT
        s.player_id,
        s.surface,
        s.surface_elo,
        RANK() OVER (ORDER BY s.surface_elo DESC) AS surface_rank
    FROM surface_ratings AS s
)
SELECT
    p.name,
    sr.surface,
    orr.overall_elo,
    sr.surface_elo,
    orr.overall_rank,
    sr.surface_rank,
    sr.surface_rank - orr.overall_rank AS rank_change
FROM overall_rankings AS orr
JOIN surface_rankings AS sr ON sr.player_id = orr.player_id
JOIN players AS p ON p.player_id = orr.player_id
ORDER BY surface_elo DESC, p.name;
