INSERT INTO head_to_head (player_id, opponent_id, surface, wins, losses, matches_played, last_updated)
WITH h2h AS (
    SELECT
        ms.player_id,
        ms.opponent_id,
        t.surface,
        COUNT(*) FILTER (WHERE ms.won) AS wins,
        COUNT(*) AS matches_played,
        NOW() AS last_updated
    FROM match_stats AS ms
    JOIN matches AS m ON ms.match_id = m.match_id
    JOIN tournaments AS t ON m.tournament_id = t.tournament_id
    WHERE t.surface IN ('Clay', 'Grass', 'Hard') AND ms.player_id = ANY(:player_ids)
    GROUP BY ms.player_id, ms.opponent_id, t.surface

    UNION ALL

    SELECT
        ms.player_id,
        ms.opponent_id,
        'ALL' AS surface,
        COUNT(*) FILTER (WHERE ms.won) AS wins,
        COUNT(*) AS matches_played,
        NOW() AS last_updated
    FROM match_stats AS ms
    WHERE ms.player_id = ANY(:player_ids)
    GROUP BY ms.player_id, ms.opponent_id
)
SELECT
    player_id,
    opponent_id,
    surface,
    wins,
    matches_played - wins AS losses,
    matches_played,
    last_updated
FROM h2h
ON CONFLICT (player_id, opponent_id, surface) DO UPDATE SET
    wins            = EXCLUDED.wins,
    losses          = EXCLUDED.losses,
    matches_played  = EXCLUDED.matches_played,
    last_updated    = EXCLUDED.last_updated