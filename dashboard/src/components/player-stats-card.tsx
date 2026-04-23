"use client"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { Surface } from "@/types/api"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

interface PlayerStatsCardProps {
  playerId: number
}

const surfaces: Surface[] = ["ALL", "Hard", "Clay", "Grass"]

export function PlayerStatsCard({ playerId }: PlayerStatsCardProps) {
  const [surface, setSurface] = useState<Surface>("ALL")
  const [season, setSeason] = useState<number>(0)

  const statsSeasonsQuery = useQuery({
    queryKey: ["player", playerId, "stats", "seasons", surface],
    queryFn: () => api.players.getStatsSeasons(playerId, surface),
    enabled: !!playerId,
  })

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["player", playerId, "stats", surface, season],
    queryFn: () => api.players.getStats(playerId, surface, season),
    enabled: !!playerId,
  })

  const formatPct = (val: number | undefined) => 
    val ? `${(val * 100).toFixed(1)}%` : "N/A"

  const formatVal = (val: number | undefined) => 
    val !== undefined ? val.toFixed(2) : "N/A"

  if (statsSeasonsQuery.isLoading) {
    return (
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="text-xl">Stats</CardTitle>
            {/* <CardDescription>Performance metrics by surface</CardDescription> */}
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (statsSeasonsQuery.error) {
    return (
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="text-xl">Stats</CardTitle>
            {/* <CardDescription>Performance metrics by surface</CardDescription> */}
          </div>
        </CardHeader>
        <CardContent>
          <div className="py-10 text-center text-sm text-red-500">
            No seasons found for this player.
          </div>
        </CardContent>
      </Card>
    )
  }

  const years = statsSeasonsQuery.data || [0]
  if (!years.includes(season)) {
    setSeason(years[years.length - 1])
  }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div>
          <CardTitle className="text-xl">Stats</CardTitle>
          {/* <CardDescription>Performance metrics by surface</CardDescription> */}
        </div>
        <div className="flex gap-2">
          <Select value={surface} onValueChange={(v) => setSurface(v as Surface)}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Surface" />
            </SelectTrigger>
            <SelectContent>
              {surfaces.map((s) => (
                <SelectItem key={s} value={s}>{s === "ALL" ? "All Surfaces" : s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={season.toString()} onValueChange={(v) => setSeason(parseInt(v))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Season" />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={y.toString()}>
                  {y === 0 ? "Career" : y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : error ? (
          <div className="py-10 text-center text-sm text-red-500">
            No stats found for this selection.
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-muted/50 p-3 rounded-lg">
              <span className="text-sm font-medium">Win/Loss Record</span>
              <span className="text-lg font-bold">
                {stats?.won} - {(stats?.matches_played ?? 0) - (stats?.won ?? 0)} ({formatPct(stats?.win_pct)})
              </span>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Service Stats</h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <StatRow label="1st Serve" value={formatPct(stats?.serve.first_serve_pct)} />
                <StatRow label="1st Serve Points Won" value={formatPct(stats?.serve.first_serve_points_won_pct)} />
                <StatRow label="2nd Serve Points Won" value={formatPct(stats?.serve.second_serve_points_won_pct)} />
                <StatRow label="Service Games Won" value={formatPct(stats?.serve.service_games_won_pct)} />
                <StatRow label="Aces / Match" value={formatVal(stats?.serve.aces_per_match)} />
                <StatRow label="Double Faults / Match" value={formatVal(stats?.serve.double_faults_per_match)} />
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Return Stats</h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <StatRow label="1st Serve Return Points Won" value={formatPct(stats?.return_.first_serve_return_points_won_pct)} />
                <StatRow label="2nd Serve Return Points Won" value={formatPct(stats?.return_.second_serve_return_points_won_pct)} />
                <StatRow label="Return Games Won" value={formatPct(stats?.return_.return_games_won_pct)} />
                <StatRow label="Break Points Converted" value={formatPct(stats?.return_.bp_conversion_pct)} />
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-muted py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  )
}
