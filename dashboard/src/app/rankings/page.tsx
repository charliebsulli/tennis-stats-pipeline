"use client"

import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { Surface } from "@/types/api"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useState } from "react"

const surfaces: Surface[] = ["ALL", "Hard", "Clay", "Grass"]

export default function RankingsPage() {
  const [surface, setSurface] = useState<Surface>("ALL")

  const { data: rankings, isLoading, error } = useQuery({
    queryKey: ["rankings", surface],
    queryFn: () => api.rankings.get(surface),
  })

  return (
    <div className="flex flex-col gap-8 py-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">ELO Rankings</h1>
        <p className="text-muted-foreground mt-2">
          Current performance-based rankings for ATP players.
        </p>
      </div>

      <Tabs
        defaultValue="ALL"
        onValueChange={(value) => setSurface(value as Surface)}
        className="w-full"
      >
        <TabsList className="grid w-full max-w-md grid-cols-4">
          {surfaces.map((s) => (
            <TabsTrigger key={s} value={s}>
              {s === "ALL" ? "All Surfaces" : s}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Rank</TableHead>
              <TableHead>Player</TableHead>
              <TableHead className="text-right">ELO Rating</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="ml-auto h-4 w-12" /></TableCell>
                </TableRow>
              ))
            ) : error ? (
              <TableRow>
                <TableCell colSpan={3} className="h-24 text-center text-red-500">
                  Error loading rankings: {(error as Error).message}
                </TableCell>
              </TableRow>
            ) : rankings?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="h-24 text-center">
                  No rankings found for this surface.
                </TableCell>
              </TableRow>
            ) : (
              rankings?.map((row) => (
                <TableRow key={row.player_id}>
                  <TableCell className="font-medium">#{row.rank}</TableCell>
                  <TableCell>
                    <Link
                      href={`/players/${row.player_id}`}
                      className="hover:text-blue-600 hover:underline"
                    >
                      {row.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {Math.round(row.elo)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
