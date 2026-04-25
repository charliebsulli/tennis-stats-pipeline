"use client"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts"

interface PlayerEloChartProps {
  playerId: number
}

export function PlayerEloChart({ playerId }: PlayerEloChartProps) {
  const [period, setPeriod] = useState<string>("career")

  const { data: history, isLoading, error } = useQuery({
    queryKey: ["player", playerId, "elo-history"],
    queryFn: () => api.players.getEloHistory(playerId, "ALL"),
    enabled: !!playerId,
  })

  // Extract unique years for the selector
  const availableYears = useMemo(() => {
    if (!history) return []
    const years = history.map(entry => new Date(entry.date).getFullYear())
    return Array.from(new Set(years)).sort((a, b) => b - a)
  }, [history])

  // Format and filter data for Recharts
  const chartData = useMemo(() => {
    if (!history) return []
    
    let filtered = [...history].reverse()
    
    if (period !== "career") {
      const selectedYear = parseInt(period)
      filtered = filtered.filter(entry => new Date(entry.date).getFullYear() === selectedYear)
    }

    return filtered.map(entry => {
      const dateObj = new Date(entry.date)
      return {
        date: dateObj.toLocaleDateString(undefined, { 
          month: 'short', 
          year: period === "career" ? 'numeric' : undefined,
          day: period !== "career" ? '2-digit' : undefined
        }),
        elo: Math.round(entry.elo),
        fullDate: entry.date.toString()
      }
    })
  }, [history, period])

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-xl">Elo History</CardTitle>
          <CardDescription>Overall rating progression over time</CardDescription>
        </div>
        {!isLoading && history && history.length > 0 && (
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="career">Career</SelectItem>
              {availableYears.map(year => (
                <SelectItem key={year} value={year.toString()}>
                  Season {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
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
            No history data available for this period.
          </div>
        ) : (
          <div className="h-[300px] w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false}
                  minTickGap={period === "career" ? 40 : 20}
                />
                <YAxis 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  domain={['auto', 'auto']}
                  padding={{ top: 10, bottom: 10 }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#fff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                  labelStyle={{ fontWeight: "bold", marginBottom: "4px" }}
                  formatter={(value: unknown) => [`${value}`, 'ELO']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="elo"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={period !== "career"}
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
