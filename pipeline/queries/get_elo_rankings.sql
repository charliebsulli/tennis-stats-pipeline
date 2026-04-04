WITH ratings AS (
    SELECT DISTINCT ON (e.player_id)
        e.player_id,
        e.elo_after
    FROM elo_history AS e
    JOIN matches AS m ON e.match_id = m.match_id
    WHERE e.surface = 'ALL'
    -- AND e.match_date >= NOW() - INTERVAL '1 year'
    ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
)
SELECT
    p.name,
    r.elo_after AS elo,
    RANK() OVER (ORDER BY r.elo_after DESC) AS rank
FROM ratings AS r
JOIN players AS p ON r.player_id = p.player_id