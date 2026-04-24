from typing import List

from api.db import get_conn
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.models.responses import MatchResponse
from sqlalchemy import text

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/recent")
async def get_recent_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn=Depends(get_conn),
) -> List[MatchResponse]:
    """Retrieve the most recently completed matches."""
    rows = conn.execute(
        text("""
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
        ORDER BY m.match_date DESC, m.round_int DESC
        LIMIT :limit OFFSET :offset
    """),
        {"limit": limit, "offset": offset},
    ).fetchall()

    return [MatchResponse.model_validate(row) for row in rows]


@router.get("/{match_id}")
async def get_match(
    match_id: int = Path(ge=1, le=2_147_483_647), conn=Depends(get_conn)
) -> MatchResponse:
    """Retrieve details for a specific match by ID."""
    row = conn.execute(
        text("""
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
        WHERE m.match_id = :match_id
    """),
        {"match_id": match_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return MatchResponse.model_validate(row)
