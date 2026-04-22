"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface PlayerEloChartProps {
  playerId: number
}

export function PlayerEloChart({ playerId }: PlayerEloChartProps) {
  const { data: history, isLoading, error } = useQuery({
    queryKey: ["player", playerId, "elo-history"],
    queryFn: () => api.players.getEloHistory(playerId, "ALL"),
    enabled: !!playerId,
  })

  // Format data for Recharts - reverse since API returns DESC
  const chartData = history 
    ? [...history].reverse().map(entry => ({
        date: new Date(entry.date).toLocaleDateString(undefined, { month: 'short', year: '2-digit' }),
        elo: Math.round(entry.elo),
        fullDate: entry.date
      }))
    : []

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-xl">ELO History</CardTitle>
        <CardDescription>Overall rating progression over time</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : error ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-red-500">
            Error loading ELO history.
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            No history data available.
          </div>
        ) : (
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false}
                  minTickGap={30}
                />
                <YAxis 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  domain={['auto', 'auto']}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#fff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                  labelStyle={{ fontWeight: "bold", marginBottom: "4px" }}
                />
                <Line
                  type="monotone"
                  dataKey="elo"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
