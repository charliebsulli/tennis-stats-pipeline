from db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from models.responses import (
    HeadToHeadResponse,
    MatchupPredictionResponse,
    Surface,
)
from sqlalchemy import text

router = APIRouter(prefix="/matchups", tags=["matchups"])


def expected_score(rating_one: float, rating_two: float) -> float:
    e = 1 / (1 + 10 ** ((rating_two - rating_one) / 400))
    return max(0.001, min(0.999, e))


@router.get("/h2h")
async def get_h2h_record(
    player_id: int,
    opponent_id: int,
    surface: Surface = Surface.all,
    conn=Depends(get_conn),
) -> HeadToHeadResponse:
    row = conn.execute(
        text("""
        SELECT
            player_id,
            opponent_id,
            surface,
            wins,
            losses,
            matches_played
        FROM head_to_head
        WHERE player_id = :p1 AND opponent_id = :p2 AND surface = :surface
    """),
        {"p1": player_id, "p2": opponent_id, "surface": surface.value},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Head to head record not found")

    return HeadToHeadResponse.model_validate(row)


@router.get("/prediction")
async def get_matchup_prediction(
    player_id: int,
    opponent_id: int,
    surface: Surface = Surface.all,
    conn=Depends(get_conn),
) -> MatchupPredictionResponse:
    if surface is Surface.all:
        query = text("""
            SELECT e.elo_after AS elo
            FROM elo_history AS e
            JOIN matches AS m ON e.match_id = m.match_id
            WHERE e.player_id = :player_id AND e.surface = 'ALL'
            ORDER BY e.match_date DESC, m.round_int DESC
            LIMIT 1
        """)
    else:
        query = text("""
            SELECT e.averaged_surface_elo AS elo
            FROM averaged_surface_elo_history AS e
            JOIN matches AS m ON e.match_id = m.match_id
            WHERE e.player_id = :player_id AND e.surface = :surface
            ORDER BY e.match_date DESC, m.round_int DESC
            LIMIT 1
        """)

    player_elo_row = conn.execute(
        query, {"player_id": player_id, "surface": surface.value}
    ).fetchone()
    if player_elo_row is None:
        raise HTTPException(
            status_code=404, detail=f"Elo rating for player {player_id} not found"
        )

    opponent_elo_row = conn.execute(
        query, {"player_id": opponent_id, "surface": surface.value}
    ).fetchone()
    if opponent_elo_row is None:
        raise HTTPException(
            status_code=404, detail=f"Elo rating for player {opponent_id} not found"
        )

    player_elo = player_elo_row.elo
    opponent_elo = opponent_elo_row.elo

    prediction = expected_score(player_elo, opponent_elo)

    return MatchupPredictionResponse(
        player_id=player_id,
        opponent_id=opponent_id,
        surface=surface,
        player_elo=player_elo,
        opponent_elo=opponent_elo,
        prediction=prediction,
    )
