from datetime import datetime, timezone

from db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from models.responses import (
    HeadToHeadResponse,
    MatchResponse,
    MatchupDetailResponse,
    MatchupPlayerDetail,
    MatchupPredictionResponse,
    PlayerFormResponse,
    Surface,
    WinLossRecord,
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
    """Get the head-to-head win/loss record between two players."""
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
    """Predict the win probability for a matchup based on current Elo ratings."""
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


async def get_player_matchup_detail(
    player_id: int, surface: Surface, conn
) -> MatchupPlayerDetail:
    # Profile Info
    player = conn.execute(
        text(
            "SELECT player_id, name, nationality, hand FROM players WHERE player_id = :id"
        ),
        {"id": player_id},
    ).fetchone()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    # Elo and Rank
    if surface is Surface.all:
        elo_query = """
            WITH latest_ratings AS (
                SELECT DISTINCT ON (e.player_id) e.player_id, e.elo_after AS elo
                FROM elo_history AS e
                JOIN matches AS m ON e.match_id = m.match_id
                WHERE e.surface = 'ALL' AND e.match_date >= NOW() - INTERVAL '1 year'
                ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
            ),
            ranked_ratings AS (
                SELECT player_id, elo, RANK() OVER (ORDER BY elo DESC) AS rank FROM latest_ratings
            )
            SELECT elo, rank FROM ranked_ratings WHERE player_id = :id
        """
    else:
        elo_query = """
            WITH latest_ratings AS (
                SELECT DISTINCT ON (e.player_id) e.player_id, e.averaged_surface_elo AS elo
                FROM averaged_surface_elo_history AS e
                JOIN matches AS m ON e.match_id = m.match_id
                WHERE e.surface = :surface AND e.match_date >= NOW() - INTERVAL '1 year'
                ORDER BY e.player_id, e.match_date DESC, m.round_int DESC
            ),
            ranked_ratings AS (
                SELECT player_id, elo, RANK() OVER (ORDER BY elo DESC) AS rank FROM latest_ratings
            )
            SELECT elo, rank FROM ranked_ratings WHERE player_id = :id
        """
    elo_row = conn.execute(
        text(elo_query), {"id": player_id, "surface": surface.value}
    ).fetchone()

    # Win/Loss Records (Season and Career)
    current_year = datetime.now(timezone.utc).year
    records_rows = conn.execute(
        text("""
            SELECT season, matches_played, won, (won::float / NULLIF(matches_played, 0)) as win_pct
            FROM player_surface_stats
            WHERE player_id = :id AND surface = :surface AND season IN (0, :year)
        """),
        {"id": player_id, "surface": surface.value, "year": current_year},
    ).fetchall()

    season_rec = WinLossRecord(matches_played=0, won=0, lost=0, win_pct=0.0)
    career_rec = WinLossRecord(matches_played=0, won=0, lost=0, win_pct=0.0)

    for row in records_rows:
        rec = WinLossRecord(
            matches_played=row.matches_played,
            won=row.won,
            lost=row.matches_played - row.won,
            win_pct=row.win_pct or 0.0,
        )
        if row.season == 0:
            career_rec = rec
        else:
            season_rec = rec

    # Form
    form_row = conn.execute(
        text(
            "SELECT player_id, surface, matches_total, won, weighted_form FROM player_form WHERE player_id = :id AND surface = :surface"
        ),
        {"id": player_id, "surface": surface.value},
    ).fetchone()
    if not form_row:
        # Fallback if no form data yet
        form = PlayerFormResponse(
            player_id=player_id,
            surface=surface,
            matches_total=0,
            won=0,
            weighted_form=0.0,
        )
    else:
        form = PlayerFormResponse.model_validate(form_row)

    return MatchupPlayerDetail(
        player_id=player.player_id,
        name=player.name,
        nationality=player.nationality or "Unknown",
        hand=player.hand or "Unknown",
        elo=None if elo_row is None else elo_row.elo,
        rank=None if elo_row is None else elo_row.rank,
        form=form,
        season_record=season_rec,
        career_record=career_rec,
    )


@router.get("/detailed")
async def get_matchup_details(
    player_id: int,
    opponent_id: int,
    surface: Surface = Surface.all,
    conn=Depends(get_conn),
) -> MatchupDetailResponse:
    """Get a detailed side-by-side comparison of two players for a matchup."""
    player_detail = await get_player_matchup_detail(player_id, surface, conn)
    opponent_detail = await get_player_matchup_detail(opponent_id, surface, conn)

    # H2H Record
    h2h_row = conn.execute(
        text("""
            SELECT player_id, opponent_id, surface, wins, losses, matches_played
            FROM head_to_head
            WHERE player_id = :p1 AND opponent_id = :p2 AND surface = :surface
        """),
        {"p1": player_id, "p2": opponent_id, "surface": surface.value},
    ).fetchone()

    if h2h_row:
        h2h = HeadToHeadResponse.model_validate(h2h_row)
    else:
        h2h = HeadToHeadResponse(
            player_id=player_id,
            opponent_id=opponent_id,
            surface=surface,
            wins=0,
            losses=0,
            matches_played=0,
        )

    # Match History
    history_rows = conn.execute(
        text("""
            SELECT
                m.match_id, m.tournament_id, t.name AS tournament_name, m.match_date,
                t.surface, m.round, m.winner_id, pw.name AS winner_name,
                m.loser_id, pl.name AS loser_name, m.score
            FROM matches AS m
            JOIN tournaments AS t ON m.tournament_id = t.tournament_id
            JOIN players AS pw ON m.winner_id = pw.player_id
            JOIN players AS pl ON m.loser_id = pl.player_id
            WHERE ((m.winner_id = :p1 AND m.loser_id = :p2) OR (m.winner_id = :p2 AND m.loser_id = :p1))
            AND (:surface = 'ALL' OR t.surface = :surface)
            ORDER BY m.match_date DESC, m.round_int DESC
        """),
        {"p1": player_id, "p2": opponent_id, "surface": surface.value},
    ).fetchall()
    match_history = [MatchResponse.model_validate(row) for row in history_rows]

    # Prediction
    prediction_val = None
    if player_detail.elo is not None and opponent_detail.elo is not None:
        prediction_val = expected_score(player_detail.elo, opponent_detail.elo)
    prediction = MatchupPredictionResponse(
        player_id=player_id,
        opponent_id=opponent_id,
        surface=surface,
        player_elo=player_detail.elo,
        opponent_elo=opponent_detail.elo,
        prediction=prediction_val,
    )

    return MatchupDetailResponse(
        player=player_detail,
        opponent=opponent_detail,
        h2h=h2h,
        prediction=prediction,
        match_history=match_history,
        surface=surface,
    )
