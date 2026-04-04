WITH latest_surface_ratings AS (
    SELECT DISTINCT ON (a.player_id, a.surface)
        a.player_id,
        a.surface,
        a.averaged_surface_elo
    FROM averaged_surface_elo_history AS a
    JOIN matches AS m ON a.match_id = m.match_id
    WHERE a.surface IN ('Clay', 'Grass', 'Hard')
    --   AND a.match_date >= NOW() - INTERVAL '1 year'
    ORDER BY a.player_id, a.surface, a.match_date DESC, m.round_int DESC
)
SELECT
    p.name,
    l.surface,
    l.averaged_surface_elo AS elo,
    RANK() OVER (
        PARTITION BY l.surface
        ORDER BY l.averaged_surface_elo DESC
    ) AS rank
FROM latest_surface_ratings AS l
JOIN players AS p ON l.player_id = p.player_id;
