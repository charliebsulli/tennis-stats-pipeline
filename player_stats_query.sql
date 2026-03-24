INSERT INTO player_surface_stats ( -- TODO I think its pointless to join players here, ms has player id
  last_updated,
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
  second_serve_points,
  service_games_won,
  second_serve_return_points
)
WITH stats AS (
  SELECT
    NOW() AS last_updated,
    p.player_id,
    t.surface,
    COALESCE(EXTRACT(YEAR FROM m.match_date)::INTEGER, 0) AS season,
    COUNT(*) AS matches_played,
    COUNT(*) FILTER (WHERE ms.won) AS won,
    SUM(ms.aces) AS aces,
    SUM(ms.double_faults) AS double_faults,
    SUM(ms.service_points) AS service_points,
    SUM(ms.first_serves_in) AS first_serves_in,
    SUM(ms.first_serve_points_won) AS first_serve_points_won,
    SUM(ms.second_serve_points_won) AS second_serve_points_won,
    SUM(ms.service_games) AS service_games,
    SUM(ms.break_points_saved) AS break_points_saved,
    SUM(ms.break_points_faced) AS break_points_faced,
    SUM(ms.return_points) AS return_points,
    SUM(ms.first_serve_return_points) AS first_serve_return_points,
    SUM(ms.first_serve_return_points_won) AS first_serve_return_points_won,
    SUM(ms.second_serve_return_points_won) AS second_serve_return_points_won,
    SUM(ms.return_games) AS return_games,
    SUM(ms.break_points_converted) AS break_points_converted,
    SUM(ms.break_points_chances) AS break_points_chances
  FROM match_stats AS ms
  JOIN players AS p ON ms.player_id = p.player_id
  JOIN matches AS m ON ms.match_id = m.match_id
  JOIN tournaments AS t ON m.tournament_id = t.tournament_id
  WHERE t.surface IN ('Clay', 'Grass', 'Hard') AND ms.complete_stats = true AND p.player_id = ANY(:player_ids)
  GROUP BY GROUPING SETS (
    (p.player_id, t.surface, EXTRACT(YEAR FROM m.match_date)),
    (p.player_id, t.surface)
    )
  
  UNION ALL
  
  SELECT
    NOW() AS last_updated,
    p.player_id,
    'ALL' as surface,
    COALESCE(EXTRACT(YEAR FROM m.match_date)::INTEGER, 0) AS season,    
    COUNT(*) AS matches_played,
    COUNT(*) FILTER (WHERE ms.won) AS won,
    SUM(ms.aces) AS aces,
    SUM(ms.double_faults) AS double_faults,
    SUM(ms.service_points) AS service_points,
    SUM(ms.first_serves_in) AS first_serves_in,
    SUM(ms.first_serve_points_won) AS first_serve_points_won,
    SUM(ms.second_serve_points_won) AS second_serve_points_won,
    SUM(ms.service_games) AS service_games,
    SUM(ms.break_points_saved) AS break_points_saved,
    SUM(ms.break_points_faced) AS break_points_faced,
    SUM(ms.return_points) AS return_points,
    SUM(ms.first_serve_return_points) AS first_serve_return_points,
    SUM(ms.first_serve_return_points_won) AS first_serve_return_points_won,
    SUM(ms.second_serve_return_points_won) AS second_serve_return_points_won,
    SUM(ms.return_games) AS return_games,
    SUM(ms.break_points_converted) AS break_points_converted,
    SUM(ms.break_points_chances) AS break_points_chances
  FROM match_stats AS ms
  JOIN players AS p ON ms.player_id = p.player_id
  JOIN matches AS m ON ms.match_id = m.match_id
  WHERE ms.complete_stats = true AND p.player_id = ANY(:player_ids)
  GROUP BY GROUPING SETS (
    (p.player_id, EXTRACT(YEAR FROM m.match_date)),
    (p.player_id)
    )
)
SELECT
  *,
  service_points - first_serves_in AS second_serve_points,
  (service_games - (break_points_faced - break_points_saved)) AS service_games_won,
  return_points - first_serve_return_points AS second_serve_return_points
FROM stats
ON CONFLICT (player_id, surface, season) DO UPDATE SET
  last_updated = EXCLUDED.last_updated,
  matches_played = EXCLUDED.matches_played,
  won = EXCLUDED.won,
  aces = EXCLUDED.aces,
  double_faults = EXCLUDED.double_faults,
  service_points = EXCLUDED.service_points,
  first_serves_in = EXCLUDED.first_serves_in,
  first_serve_points_won = EXCLUDED.first_serve_points_won,
  second_serve_points_won = EXCLUDED.second_serve_points_won,
  service_games = EXCLUDED.service_games,
  break_points_saved = EXCLUDED.break_points_saved,
  break_points_faced = EXCLUDED.break_points_faced,
  return_points = EXCLUDED.return_points,
  first_serve_return_points = EXCLUDED.first_serve_return_points,
  first_serve_return_points_won = EXCLUDED.first_serve_return_points_won,
  second_serve_return_points_won = EXCLUDED.second_serve_return_points_won,
  return_games = EXCLUDED.return_games,
  break_points_converted = EXCLUDED.break_points_converted,
  break_points_chances = EXCLUDED.break_points_chances,
  second_serve_points = EXCLUDED.second_serve_points,
  service_games_won = EXCLUDED.service_games_won,
  second_serve_return_points = EXCLUDED.second_serve_return_points;