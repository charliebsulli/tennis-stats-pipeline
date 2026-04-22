"use client"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"
import { useParams } from "next/navigation"

export default function PlayerProfile() {
  const params = useParams()
  const playerId = parseInt(params.id as string)

  const { data: player, isLoading, error } = useQuery({
    queryKey: ["player", playerId],
    queryFn: () => api.players.get(playerId),
    enabled: !!playerId,
  })

  if (isLoading) {
    return (
      <div className="py-8">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-64" />
            <Skeleton className="mt-2 h-4 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-48" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-8 text-center text-red-500">
        Error loading player profile: {(error as Error).message}
      </div>
    )
  }

  if (!player) return null

  return (
    <div className="py-8">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-3xl">{player.name}</CardTitle>
              {/* <CardDescription>Player ID: #{player.player_id}</CardDescription> */}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Nationality</dt>
              <dd className="mt-1 text-lg">{player.nationality || "Unknown"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Plays</dt>
              <dd className="mt-1 text-lg">
                {player.hand === "R" ? "Right-handed" : player.hand === "L" ? "Left-handed" : "Unknown"}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}
