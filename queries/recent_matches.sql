SELECT player_id, 'ALL' AS surface, match_date, won
FROM (
    SELECT
        ms.player_id,
        'ALL' AS surface,
        m.match_date,
        ms.won,
        ROW_NUMBER() OVER (
            PARTITION BY ms.player_id
            ORDER BY m.match_date DESC, m.round_int DESC
        ) AS rn
    FROM match_stats AS ms
    JOIN matches AS m ON ms.match_id = m.match_id
    WHERE match_date >= NOW() - INTERVAL '90 days'
)
WHERE rn <= 20

UNION ALL

SELECT player_id, surface, match_date, won
FROM (
    SELECT
        ms.player_id,
        t.surface,
        m.match_date,
        ms.won,
        ROW_NUMBER() OVER (
            PARTITION BY ms.player_id, t.surface
            ORDER BY m.match_date DESC, m.round_int DESC
        ) AS rn
    FROM match_stats AS ms
    JOIN matches AS m ON ms.match_id = m.match_id
    JOIN tournaments AS t ON m.tournament_id = t.tournament_id
    WHERE match_date >= NOW() - INTERVAL '90 days'
)
WHERE rn <= 20
AND surface IN ('Clay', 'Hard', 'Grass')