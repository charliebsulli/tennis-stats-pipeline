import { EloRankingEntry, Surface, Player, PlayerStats, EloHistoryEntry, Match, EloResponse, PlayerForm } from "@/types/api"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }))
    throw new Error(error.detail || response.statusText)
  }
  return response.json()
}

export const api = {
  rankings: {
    get: (surface: Surface = "ALL"): Promise<EloRankingEntry[]> =>
      fetch(`${API_BASE_URL}/rankings/?surface=${surface}`).then(handleResponse),
  },
  players: {
    search: (name: string): Promise<Player[]> =>
      fetch(`${API_BASE_URL}/players/search?name=${name}`).then(handleResponse),
    get: (id: number): Promise<Player> =>
      fetch(`${API_BASE_URL}/players/${id}`).then(handleResponse),
    getElo: (id: number, surface: Surface = "ALL"): Promise<EloResponse> =>
      fetch(`${API_BASE_URL}/players/${id}/elo?surface=${surface}`).then(handleResponse),
    getForm: (id: number, surface: Surface = "ALL"): Promise<PlayerForm> =>
      fetch(`${API_BASE_URL}/players/${id}/form?surface=${surface}`).then(handleResponse),
    getStats: (id: number, surface: Surface = "ALL", season: number = 0): Promise<PlayerStats> =>
      fetch(`${API_BASE_URL}/players/${id}/stats?surface=${surface}&season=${season}`).then(handleResponse),
    getEloHistory: (id: number, surface: Surface = "ALL"): Promise<EloHistoryEntry[]> =>
      fetch(`${API_BASE_URL}/players/${id}/elo/history?surface=${surface}`).then(handleResponse),
    getMatches: (id: number, limit = 20): Promise<Match[]> =>
      fetch(`${API_BASE_URL}/players/${id}/matches?limit=${limit}`).then(handleResponse),
  },
  matchups: {
    getDetailed: (p1: number, p2: number, surface: Surface = "ALL") =>
      fetch(`${API_BASE_URL}/matchups/detailed?player_id=${p1}&opponent_id=${p2}&surface=${surface}`).then(handleResponse),
  }
}
