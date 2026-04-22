"use client"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
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

  if (playerQuery.error) {
    return (
      <div className="py-8 text-center text-red-500">
        Error loading player profile: {(playerQuery.error as Error).message}
      </div>
    )
  }

  if (!playerQuery.data) return null

  return (
<div className="py-8">
  <Card>
    <CardHeader>
      <CardTitle className="text-3xl mb-4">{playerQuery.data.name}</CardTitle>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {eloQuery.isLoading ? (
          <>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </>
        ) : eloQuery.error ? (
          <div className="col-span-2 bg-muted rounded-lg p-3 text-center border border-red-100">
            <p className="text-sm text-red-500">Elo unavailable</p>
          </div>
        ) : (
          <>
            <div className="bg-muted rounded-lg p-3 text-center">
              <p className="text-2xl font-medium">#{eloQuery.data?.rank}</p>
              <p className="text-xs text-muted-foreground mt-1">Elo Rank</p>
            </div>
            <div className="bg-muted rounded-lg p-3 text-center">
              <p className="text-2xl font-medium">{Math.round(eloQuery.data?.elo ?? 0)}</p>
              <p className="text-xs text-muted-foreground mt-1">Elo Rating</p>
            </div>
          </>
        )}
        
        {formQuery.isLoading ? (
          <>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </>
        ) : formQuery.error ? (
          <div className="col-span-2 bg-muted rounded-lg p-3 text-center border border-red-100">
            <p className="text-sm text-red-500">Form unavailable</p>
          </div>
        ) : (
          <>
            <div className="bg-muted rounded-lg p-3 text-center">
              <p className="text-2xl font-medium">{Math.round((formQuery.data?.weighted_form ?? 0) * 100)}</p>
              <p className="text-xs text-muted-foreground mt-1">Form Score (90d)</p>
            </div>
            <div className="bg-muted rounded-lg p-3 text-center">
              <p className="text-2xl font-medium">
                {formQuery.data?.won}-{ (formQuery.data?.matches_total ?? 0) - (formQuery.data?.won ?? 0) }
              </p>
              <p className="text-xs text-muted-foreground mt-1">W-L (90d)</p>
            </div>
          </>
        )}
      </div>
    </CardHeader>
    <CardContent>
      <Separator className="mb-4" />
      <dl className="flex gap-8">
        <div>
          <dt className="text-xs text-muted-foreground">Nationality</dt>
          <dd className="mt-1 text-base">{playerQuery.data.nationality || "Unknown"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Plays</dt>
          <dd className="mt-1 text-base">
            {playerQuery.data.hand === "R" ? "Right-handed" : playerQuery.data.hand === "L" ? "Left-handed" : "Unknown"}
          </dd>
        </div>
      </dl>
    </CardContent>
  </Card>
</div>
  )
}
