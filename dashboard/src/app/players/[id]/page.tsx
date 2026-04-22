"use client"

import { useParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Skeleton } from "@/components/ui/skeleton"
import { PlayerHeader } from "@/components/player-header"
import { PlayerStatsCard } from "@/components/player-stats-card"
import { PlayerEloChart } from "@/components/player-elo-chart"
import { MatchHistory } from "@/components/match-history"

export default function PlayerProfile() {
  const params = useParams()
  const playerId = parseInt(params.id as string)

  const playerQuery = useQuery({
    queryKey: ["player", playerId],
    queryFn: () => api.players.get(playerId),
    enabled: !!playerId,
  })

  const eloQuery = useQuery({
    queryKey: ["player", playerId, "elo"],
    queryFn: () => api.players.getElo(playerId),
    enabled: !!playerId,
  })

  const formQuery = useQuery({
    queryKey: ["player", playerId, "form"],
    queryFn: () => api.players.getForm(playerId),
    enabled: !!playerId,
  })

  const matchesQuery = useQuery({
    queryKey: ["player", playerId, "matches"],
    queryFn: () => api.players.getMatches(playerId),
    enabled: !!playerId,
  })

  if (playerQuery.isLoading) {
    return (
      <div className="py-8 space-y-6">
        <Skeleton className="h-[280px] w-full rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-[400px] w-full rounded-xl" />
          <Skeleton className="h-[400px] w-full rounded-xl" />
        </div>
        <Skeleton className="h-[500px] w-full rounded-xl" />
      </div>
    )
  }

  if (playerQuery.error) {
    return (
      <div className="py-8 text-center text-red-500">
        Error loading player profile: {(playerQuery.error as Error).message}
      </div>
    )
  }

  if (!playerQuery.data) return null

  return (
    <div className="py-8 space-y-6">
      <PlayerHeader 
        player={playerQuery.data} 
        elo={eloQuery.data}
        form={formQuery.data}
        eloLoading={eloQuery.isLoading}
        formLoading={formQuery.isLoading}
        eloError={eloQuery.error}
        formError={formQuery.error}
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlayerStatsCard playerId={playerId} />
        <PlayerEloChart playerId={playerId} />
      </div>

      {matchesQuery.isLoading ? (
        <Skeleton className="h-[500px] w-full rounded-xl" />
      ) : matchesQuery.error ? (
        <div className="text-center text-red-500 py-10 border rounded-xl bg-muted/20">
          Error loading match history.
        </div>
      ) : (
        <MatchHistory 
          matches={matchesQuery.data || []} 
          currentPlayerId={playerId} 
        />
      )}
    </div>
  )
}
