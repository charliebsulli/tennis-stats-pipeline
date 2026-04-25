"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface MatchHistoryProps {
  playerId: number
  title?: string
  initialLimit?: number
}

export function MatchHistory({ 
  playerId, 
  title = "Recent Matches", 
  initialLimit = 10
}: MatchHistoryProps) {
  const [page, setPage] = useState(0)
  const limit = initialLimit

  const { data: matches, isLoading, error } = useQuery({
    queryKey: ["player", playerId, "matches", page, limit],
    queryFn: () => api.players.getMatches(playerId, limit, page * limit),
    enabled: !!playerId,
  })

  const hasNextPage = matches && matches.length === limit

  const handlePrevious = () => setPage(p => Math.max(0, p - 1))
  const handleNext = () => hasNextPage && setPage(p => p + 1)

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Tournament</TableHead>
                <TableHead>Round</TableHead>
                <TableHead>Opponent</TableHead>
                <TableHead>Result</TableHead>
                <TableHead className="text-right">Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: limit }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={6}><Skeleton className="h-6 w-full" /></TableCell>
                  </TableRow>
                ))
              ) : error ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-red-500">
                    Error loading matches.
                  </TableCell>
                </TableRow>
              ) : !matches || matches.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    No matches found.
                  </TableCell>
                </TableRow>
              ) : (
                matches.map((match) => {
                  const isWinner = playerId === match.winner_id
                  const opponentName = isWinner ? match.loser_name : match.winner_name
                  const opponentId = isWinner ? match.loser_id : match.winner_id

                  return (
                    <TableRow key={match.match_id}>
                      <TableCell className="whitespace-nowrap font-medium text-muted-foreground">
                        {new Date(match.match_date).toLocaleDateString(undefined, { 
                          month: 'short', 
                          day: 'numeric', 
                          year: 'numeric' 
                        })}
                      </TableCell>
                      <TableCell className="max-w-[150px] truncate font-medium">
                        {match.tournament_name}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {match.round}
                      </TableCell>
                      <TableCell>
                        <Link 
                          href={`/players/${opponentId}`}
                          className="font-medium hover:text-blue-600 hover:underline"
                        >
                          {opponentName}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <span className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
                          isWinner ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        )}>
                          {isWinner ? 'W' : 'L'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {match.score}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      {!isLoading && !error && (matches?.length || 0) > 0 && (
        <CardFooter className="flex items-center justify-between border-t py-4">
          <div className="text-sm text-muted-foreground">
            Page {page + 1}
          </div>
          <Pagination className="mx-0 w-auto">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={handlePrevious} 
                  className={cn(
                    "cursor-pointer",
                    page === 0 && "pointer-events-none opacity-50"
                  )}
                />
              </PaginationItem>
              <PaginationItem>
                <PaginationNext 
                  onClick={handleNext}
                  className={cn(
                    "cursor-pointer",
                    !hasNextPage && "pointer-events-none opacity-50"
                  )}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </CardFooter>
      )}
    </Card>
  )
}
