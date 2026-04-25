"use client"

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
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
import { cn } from "@/lib/utils"
import { Surface } from "@/types/api"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useEffect, useState } from "react"

const surfaces: Surface[] = ["ALL", "Hard", "Clay", "Grass"]
const LIMIT = 100

export default function RankingsPage() {
  const [surface, setSurface] = useState<Surface>("ALL")
  const [page, setPage] = useState(0)

  // Reset page when surface changes
  useEffect(() => {
    setPage(0)
  }, [surface])

  const { data: rankings, isLoading, error } = useQuery({
    queryKey: ["rankings", surface, page],
    queryFn: () => api.rankings.get(surface, LIMIT, page * LIMIT),
  })

  const hasNextPage = rankings && rankings.length === LIMIT

  return (
    <div className="flex flex-col gap-8 py-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Elo Rankings</h1>
          <p className="text-muted-foreground mt-2">
            Players active within the last year ranked by Elo rating on each surface. Rankings are updated daily.
          </p>
        </div>

        <Tabs
          defaultValue="ALL"
          onValueChange={(value) => setSurface(value as Surface)}
          className="w-full max-w-md"
        >
          <TabsList className="grid w-full grid-cols-4">
            {surfaces.map((s) => (
              <TabsTrigger key={s} value={s}>
                {s === "ALL" ? "Overall" : s}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <div className="rounded-md border bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Rank</TableHead>
              <TableHead>Player</TableHead>
              <TableHead className="text-right">Elo Rating</TableHead>
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

        {!isLoading && !error && (rankings?.length || 0) > 0 && (
          <div className="flex items-center justify-between border-t px-4 py-4">
            <div className="text-sm text-muted-foreground">
              Showing rankings {page * LIMIT + 1} - {page * LIMIT + (rankings?.length || 0)}
            </div>
            <Pagination className="mx-0 w-auto">
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious 
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    className={cn(
                      "cursor-pointer",
                      page === 0 && "pointer-events-none opacity-50"
                    )}
                  />
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext 
                    onClick={() => setPage(p => p + 1)}
                    className={cn(
                      "cursor-pointer",
                      !hasNextPage && "pointer-events-none opacity-50"
                    )}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}
      </div>
    </div>
  )
}
