from typing import List

from db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from models.responses import (
    EloHistoryEntry,
    EloResponse,
    MatchResponse,
    Player,
    PlayerFormResponse,
    PlayerStatsResponse,
    ReturnStats,
    ServeStats,
    Surface,
)
from sqlalchemy import text

router = APIRouter(prefix="/players")


@router.get("/search")
async def search_players(name: str, conn=Depends(get_conn)) -> List[Player]:
    rows = conn.execute(
        text("""
        SELECT player_id, name, nationality, hand
        FROM players
        WHERE name ILIKE :name
        ORDER BY name
        LIMIT 20
    """),
        {"name": f"%{name}%"},
    ).fetchall()

    return [Player.model_validate(row) for row in rows]


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
    player_id: int,
    surface: Surface = Surface.all,
    season: int = 0,
    conn=Depends(get_conn),
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


@router.get("/{player_id}/elo")
async def get_player_elo(
    player_id: int, surface: Surface = Surface.all, conn=Depends(get_conn)
) -> EloResponse:
    query = ""
    if surface is Surface.all:
        query += """
        WITH latest_ratings AS (
            SELECT DISTINCT ON (e.player_id)
                e.player_id,
                e.elo_after AS elo
            FROM elo_history AS e
            JOIN matches AS m ON e.match_id = m.match_id
            WHERE e.surface = :surface AND e.match_date >= NOW() - INTERVAL '1 year'
            ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
        ),
        """
    else:
        query += """
        WITH latest_ratings AS (
            SELECT DISTINCT ON (e.player_id)
                e.player_id,
                e.averaged_surface_elo AS elo
            FROM averaged_surface_elo_history AS e
            JOIN matches AS m ON e.match_id = m.match_id
            WHERE e.surface = :surface AND e.match_date >= NOW() - INTERVAL '1 year'
            ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
        ),
        """
    row = conn.execute(
        text(
            query
            + """
        ranked_ratings AS (
            SELECT
                player_id,
                elo,
                RANK() OVER (ORDER BY elo DESC) AS rank
            FROM latest_ratings
        )
        SELECT player_id, elo, rank
        FROM ranked_ratings
        WHERE player_id = :player_id
        """
        ),
        {"player_id": player_id, "surface": surface.value},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Elo ranking not found")

    return EloResponse(
        player_id=row.player_id,
        surface=surface,
        elo=row.elo,
        rank=row.rank,
    )


@router.get(
    "/{player_id}/elo/history"
)  # TODO history can look ambiguous since multiple matches w/ same date in old data
async def get_player_elo_history(
    player_id: int, surface: Surface = Surface.all, conn=Depends(get_conn)
) -> List[EloHistoryEntry]:
    query = ""
    if surface is Surface.all:
        query += """
        SELECT
            e.match_date AS date,
            e.surface,
            e.elo_after AS elo
        FROM elo_history AS e
        """
    else:
        query += """
        SELECT
            e.match_date as date,
            e.surface,
            e.averaged_surface_elo as elo
        FROM averaged_surface_elo_history as e
        """
    rows = conn.execute(
        text(
            query
            + """
        WHERE e.player_id = :player_id
        AND e.surface = :surface
        ORDER BY e.match_date DESC, e.match_id DESC
        """
        ),
        {"player_id": player_id, "surface": surface.value},
    ).fetchall()

    return [EloHistoryEntry.model_validate(row) for row in rows]


@router.get("/{player_id}/form")
async def get_player_form(
    player_id: int, surface: Surface = Surface.all, conn=Depends(get_conn)
) -> PlayerFormResponse:
    row = conn.execute(
        text("""
        SELECT
            player_id,
            surface,
            matches_total,
            won,
            weighted_form
        FROM player_form
        WHERE player_id = :player_id
        AND surface = :surface
        """),
        {"player_id": player_id, "surface": surface.value},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Form data not found")

    return PlayerFormResponse.model_validate(row)


@router.get("/{player_id}/matches")
async def get_player_matches(
    player_id: int,
    surface: Surface = Surface.all,
    limit: int = 20,
    conn=Depends(get_conn),
) -> List[MatchResponse]:
    query = """
        SELECT
            m.match_id,
            m.tournament_id,
            t.name AS tournament_name,
            m.match_date,
            t.surface,
            m.round,
            m.winner_id,
            pw.name AS winner_name,
            m.loser_id,
            pl.name AS loser_name,
            m.score
        FROM matches AS m
        JOIN tournaments AS t ON m.tournament_id = t.tournament_id
        JOIN players AS pw ON m.winner_id = pw.player_id
        JOIN players AS pl ON m.loser_id = pl.player_id
        WHERE (m.winner_id = :player_id OR m.loser_id = :player_id)
    """
    params = {"player_id": player_id, "limit": limit}

    if surface != Surface.all:
        query += " AND t.surface = :surface"
        params["surface"] = surface.value

    query += " ORDER BY m.match_date DESC, m.round_int DESC LIMIT :limit"

    rows = conn.execute(text(query), params).fetchall()

    return [MatchResponse.model_validate(row) for row in rows]
