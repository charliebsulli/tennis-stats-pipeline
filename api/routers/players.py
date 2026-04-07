from db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from models.responses import (
    Player,
    PlayerStatsResponse,
    ReturnStats,
    ServeStats,
    Surface,
)
from sqlalchemy import text

router = APIRouter(prefix="/players")


@router.get("/{player_id}")
async def get_player(player_id: int, conn=Depends(get_conn)) -> Player:
    row = conn.execute(
        text("""
        SELECT player_id, name, nationality, hand
        FROM players
        WHERE player_id = :player_id
    """),
        {"player_id": player_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return Player.model_validate(row)


@router.get("/{player_id}/stats")
async def get_player_stats(
    player_id: int, surface: Surface = all, season: int = 0, conn=Depends(get_conn)
) -> PlayerStatsResponse:
    row = conn.execute(
        text("""
        SELECT
            player_id,
            surface,
            season,
            matches_played,
            won,
            won::float / NULLIF(matches_played, 0)                                          AS win_pct,

            -- aces and double faults
            aces,
            double_faults,
            aces::float / NULLIF(matches_played, 0)                                         AS aces_per_match,
            double_faults::float / NULLIF(matches_played, 0)                                AS double_faults_per_match,

            -- first serve
            first_serves_in,
            service_points,
            first_serves_in::float / NULLIF(service_points, 0)                             AS first_serve_pct,

            -- first serve points won
            first_serve_points_won,
            first_serve_points_won::float / NULLIF(first_serves_in, 0)                     AS first_serve_points_won_pct,

            -- second serve points won
            second_serve_points_won,
            second_serve_points,
            second_serve_points_won::float / NULLIF(second_serve_points, 0)                AS second_serve_points_won_pct,

            -- service games won
            service_games_won,
            service_games,
            service_games_won::float / NULLIF(service_games, 0)                            AS service_games_won_pct,

            -- break points saved
            break_points_saved,
            break_points_faced,
            break_points_saved::float / NULLIF(break_points_faced, 0)                      AS bp_save_pct,

            -- first serve return points won
            first_serve_return_points_won,
            first_serve_return_points,
            first_serve_return_points_won::float / NULLIF(first_serve_return_points, 0)    AS first_serve_return_points_won_pct,

            -- second serve return points won
            second_serve_return_points_won,
            second_serve_return_points,
            second_serve_return_points_won::float / NULLIF(second_serve_return_points, 0)  AS second_serve_return_points_won_pct,

            -- break points converted
            break_points_converted,
            break_points_chances,
            break_points_converted::float / NULLIF(break_points_chances, 0)                AS bp_conversion_pct,

            -- return games won
            return_games,
            break_points_converted::float / NULLIF(return_games, 0)                        AS return_games_won_pct
        FROM player_surface_stats
        WHERE player_id = :player_id
        AND surface = :surface
        AND season = :season
        """),
        {
            "player_id": player_id,
            "surface": surface.value,
            "season": season,
        },
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Stats not found")

    return PlayerStatsResponse(
        player_id=row.player_id,
        surface=row.surface,
        season=row.season,
        matches_played=row.matches_played,
        won=row.won,
        win_pct=row.win_pct,
        serve=ServeStats.model_validate(row),
        return_=ReturnStats.model_validate(row),
    )
