export type Surface = "ALL" | "Hard" | "Clay" | "Grass"

export interface Player {
  player_id: number
  name: string
  nationality: string
  hand: string
}

export interface EloRankingEntry {
  player_id: number
  name: string
  surface: Surface
  elo: number
  rank: number
}

export interface EloHistoryEntry {
  date: string
  surface: Surface
  elo: number
}

export interface WinLossRecord {
  matches_played: number
  won: number
  lost: number
  win_pct: number
}

export interface EloResponse {
  player_id: number
  surface: Surface
  elo: number
  rank: number
}

export interface PlayerForm {
  player_id: number
  surface: Surface
  matches_total: number
  won: number
  weighted_form: number
}

export interface PlayerStats {
  player_id: number
  surface: Surface
  season: number
  matches_played: number
  won: number
  win_pct: number
  serve: {
    aces: number
    double_faults: number
    aces_per_match: number
    double_faults_per_match: number
    first_serve_pct: number
    first_serve_points_won_pct: number
    second_serve_points_won_pct: number
    service_games_won_pct: number
    bp_save_pct: number
  }
  return_: {
    first_serve_return_points_won_pct: number
    second_serve_return_points_won_pct: number
    bp_conversion_pct: number
    return_games_won_pct: number
  }
}

export interface Match {
  match_id: number
  tournament_id: string
  tournament_name: string
  match_date: string
  surface: Surface
  round: string
  winner_id: number
  winner_name: string
  loser_id: number
  loser_name: string
  score: string
}

export interface HeadToHead {
  player_id: number
  opponent_id: number
  surface: Surface
  wins: number
  losses: number
  matches_played: number
}

export interface MatchupPrediction {
  player_id: number
  opponent_id: number
  surface: Surface
  player_elo: number | null
  opponent_elo: number | null
  prediction: number | null
}

export interface MatchupPlayerDetail {
  player_id: number
  name: string
  nationality: string
  hand: string
  elo: number | null
  rank: number | null
  form: PlayerForm
  season_record: WinLossRecord
  career_record: WinLossRecord
}

export interface MatchupDetail {
  player: MatchupPlayerDetail
  opponent: MatchupPlayerDetail
  h2h: HeadToHead
  prediction: MatchupPrediction
  match_history: Match[]
  surface: Surface
}
