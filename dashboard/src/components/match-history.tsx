import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { Match } from "@/types/api"
import Link from "next/link"

interface MatchHistoryProps {
  matches: Match[]
  title?: string
  description?: string
  currentPlayerId?: number
}

export function MatchHistory({ 
  matches, 
  title = "Recent Matches", 
  description = "Latest results from the ATP tour",
  currentPlayerId 
}: MatchHistoryProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
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
              {matches.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    No matches found.
                  </TableCell>
                </TableRow>
              ) : (
                matches.map((match) => {
                  const isWinner = currentPlayerId === match.winner_id
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
                        {currentPlayerId ? (
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
                            isWinner ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                          )}>
                            {isWinner ? 'W' : 'L'}
                          </span>
                        ) : (
                          <span className="text-xs font-medium text-muted-foreground">
                            {match.winner_name} def.
                          </span>
                        )}
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
    </Card>
  )
}
