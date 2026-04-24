from datetime import date, datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from api.db import get_conn
from api.models.responses import EloRankingEntry, Surface

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/")
async def get_elo_rankings(
    surface: Surface = Surface.all,
    date: date | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn=Depends(get_conn),
) -> List[EloRankingEntry]:
    """Retrieve the top Elo-ranked players for a specific surface and date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    query = ""
    if surface is Surface.all:
        query += """WITH ratings AS (
                    SELECT DISTINCT ON (e.player_id)
                        e.player_id,
                        e.elo_after AS elo,
                        e.surface
                    FROM elo_history AS e
                    JOIN matches AS m
                        ON e.match_id = m.match_id
                    WHERE
                        e.surface = 'ALL'
                        AND m.match_date >= :date - INTERVAL '1 year'
                        AND m.match_date <= :date
                    ORDER BY
                        e.player_id,
                        m.match_date DESC,
                        m.round_int DESC
                    )"""
    else:
        query += """WITH ratings AS (
                    SELECT DISTINCT ON (e.player_id)
                        e.player_id,
                        e.averaged_surface_elo AS elo,
                        e.surface
                    FROM averaged_surface_elo_history AS e
                    JOIN matches AS m
                        ON e.match_id = m.match_id
                    WHERE
                        e.surface = :surface
                        AND m.match_date >= :date - INTERVAL '1 year'
                        AND m.match_date <= :date
                    ORDER BY
                        e.player_id,
                        m.match_date DESC,
                        m.round_int DESC
                    )"""
    query += """SELECT
                    r.player_id,
                    p.name,
                    r.surface,
                    r.elo,
                    RANK() OVER (ORDER BY r.elo DESC) AS rank
                FROM ratings AS r
                JOIN players AS p
                    ON r.player_id = p.player_id
                ORDER BY rank ASC
                LIMIT :limit OFFSET :offset;"""
    rows = conn.execute(
        text(query),
        {"surface": surface.value, "date": date, "limit": limit, "offset": offset},
    ).fetchall()

    return [EloRankingEntry.model_validate(row) for row in rows]
