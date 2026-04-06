from db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

router = APIRouter(prefix="/players")


@router.get("/{player_id}")
async def get_player(player_id: int, conn=Depends(get_conn)):
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

    return {
        "player_id": row.player_id,
        "name": row.name,
        "nationality": row.nationality,
        "hand": row.hand,
    }
