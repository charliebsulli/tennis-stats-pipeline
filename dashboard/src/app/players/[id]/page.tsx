"use client"

import { MatchHistory } from "@/components/match-history"
import { PlayerEloChart } from "@/components/player-elo-chart"
import { PlayerHeader } from "@/components/player-header"
import { PlayerSearch } from "@/components/player-search"
import { PlayerStatsCard } from "@/components/player-stats-card"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"
import { useParams } from "next/navigation"

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

  if (playerQuery.isLoading) {
    return (
      <div className="py-8 space-y-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-10 w-[300px]" />
        </div>
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PlayerSearch />
      </div>

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

      <MatchHistory 
        playerId={playerId} 
        title="Latest Results"
      />
    </div>
  )
}
