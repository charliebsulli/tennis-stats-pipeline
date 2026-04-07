from datetime import date
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict


# TODO does this belong here
class Surface(str, Enum):
    all = "ALL"
    clay = "Clay"
    grass = "Grass"
    hard = "Hard"


def round3(v: Optional[float]) -> Optional[float]:
    if v is None:
        return v
    return round(v, 3)


RoundedFloat = Annotated[Optional[float], AfterValidator(round3)]


class Player(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    name: str
    nationality: str
    hand: str


class ServeStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aces: int
    aces_per_match: RoundedFloat

    double_faults: int
    double_faults_per_match: RoundedFloat

    first_serves_in: int
    service_points: int
    first_serve_pct: RoundedFloat

    first_serve_points_won: int
    first_serve_points_won_pct: RoundedFloat

    second_serve_points_won: int
    second_serve_points: int
    second_serve_points_won_pct: RoundedFloat

    service_games_won: int
    service_games: int
    service_games_won_pct: RoundedFloat

    break_points_saved: int
    break_points_faced: int
    bp_save_pct: RoundedFloat


class ReturnStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_serve_return_points_won: int
    first_serve_return_points: int
    first_serve_return_points_won_pct: RoundedFloat

    second_serve_return_points_won: int
    second_serve_return_points: int
    second_serve_return_points_won_pct: RoundedFloat

    break_points_converted: int
    break_points_chances: int
    bp_conversion_pct: RoundedFloat

    return_games: int
    return_games_won_pct: RoundedFloat


class PlayerStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    surface: Surface
    season: int

    matches_played: int
    won: int
    win_pct: RoundedFloat

    serve: ServeStats
    return_: ReturnStats

    model_config = ConfigDict(from_attributes=True)


class EloResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    player_id: int
    surface: Surface
    elo: float
    rank: int


class EloHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    surface: Surface
    elo: float


class PlayerFormResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    player_id: int
    surface: Surface
    matches_total: int
    won: int
    weighted_form: RoundedFloat


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    match_id: int
    tournament_id: str
    tournament_name: str
    match_date: date
    surface: Surface
    round: str
    winner_id: int
    winner_name: str
    loser_id: int
    loser_name: str
    score: str


class EloRankingEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    player_id: int
    name: str
    surface: Surface
    elo: float
    rank: int
