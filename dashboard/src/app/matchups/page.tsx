"use client"

import { PlayerSearch } from "@/components/player-search"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Match, MatchupDetail, Player, Surface } from "@/types/api"
import { useQuery } from "@tanstack/react-query"
import { BarChart3, History, Trophy, User } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

export default function MatchupsPage() {
  const [player1, setPlayer1] = useState<Player | null>(null)
  const [player2, setPlayer2] = useState<Player | null>(null)
  const [surface, setSurface] = useState<Surface>("ALL")

  const { data: matchup, isLoading, error } = useQuery({
    queryKey: ["matchup", player1?.player_id, player2?.player_id, surface],
    queryFn: () => api.matchups.getDetailed(player1!.player_id, player2!.player_id, surface),
    enabled: !!player1 && !!player2,
  })

  const handleSetPlayer1 = (player: Player) => {
    if (player2 && player.player_id === player2.player_id) {
      alert("Please select a different player.")
      return
    }
    setPlayer1(player)
  }

  const handleSetPlayer2 = (player: Player) => {
    if (player1 && player.player_id === player1.player_id) {
      alert("Please select a different player.")
      return
    }
    setPlayer2(player)
  }

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Head to Head</h1>
          <p className="text-muted-foreground">Compare players and see win probabilities.</p>
        </div>
        
        <Tabs value={surface} onValueChange={(v) => setSurface(v as Surface)} className="w-full md:w-auto">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="ALL">All</TabsTrigger>
            <TabsTrigger value="Hard">Hard</TabsTrigger>
            <TabsTrigger value="Clay">Clay</TabsTrigger>
            <TabsTrigger value="Grass">Grass</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <label className="text-sm font-medium">Player 1</label>
          {player1 ? (
            <SelectedPlayerCard player={player1} onClear={() => setPlayer1(null)} />
          ) : (
            <PlayerSearch onSelect={handleSetPlayer1} placeholder="Search for first player..." />
          )}
        </div>
        <div className="space-y-4">
          <label className="text-sm font-medium">Player 2</label>
          {player2 ? (
            <SelectedPlayerCard player={player2} onClear={() => setPlayer2(null)} />
          ) : (
            <PlayerSearch onSelect={handleSetPlayer2} placeholder="Search for second player..." />
          )}
        </div>
      </div>

      {!player1 || !player2 ? (
        <Card className="bg-muted/50 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <User className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">Select two players to compare</h3>
            <p className="text-sm text-muted-foreground max-w-sm mt-2">
              Use the search boxes above to find and select two players for a detailed head-to-head analysis.
            </p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="space-y-8">
          <Skeleton className="h-[400px] w-full" />
          <Skeleton className="h-[300px] w-full" />
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="py-10 text-center text-destructive">
            <p>Error loading matchup data. Please try again.</p>
          </CardContent>
        </Card>
      ) : matchup ? (
        <div className="space-y-8 animate-in fade-in duration-500">
          <H2HOverview matchup={matchup} />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <H2HStatsComparison matchup={matchup} />
            <H2HMatchHistory history={matchup.match_history} p1Id={player1.player_id} />
          </div>
        </div>
      ) : null}
    </div>
  )
}

function SelectedPlayerCard({ player, onClear }: { player: Player, onClear: () => void }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
          {player.name.charAt(0)}
        </div>
        <div>
          <Link href={`/players/${player.player_id}`} className="hover:underline">
            <h4 className="font-semibold">{player.name}</h4>
          </Link>
          <p className="text-xs text-muted-foreground">{player.nationality}</p>
        </div>
      </div>
      <button 
        onClick={onClear}
        className="text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        Change
      </button>
    </div>
  )
}

function H2HOverview({ matchup }: { matchup: MatchupDetail }) {
  const { player, opponent, h2h, prediction } = matchup
  
  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-muted/30 border-b">
        <div className="flex items-center justify-center gap-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
          <Trophy className="h-4 w-4" />
          Head to Head Record
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="flex flex-col md:flex-row items-stretch">
          {/* Player 1 */}
          <div className="flex-1 p-8 flex flex-col items-center text-center space-y-4">
            <span className="text-4xl font-black text-primary">{h2h.wins}</span>
            <div className="space-y-1">
              <h2 className="text-2xl font-bold">{player.name}</h2>
              <p className="text-sm text-muted-foreground">{player.nationality} • {player.hand === 'R' ? 'Right' : 'Left'}-handed</p>
            </div>
          </div>

          {/* VS Divider */}
          <div className="flex flex-col items-center justify-center p-4 bg-muted/10 border-x border-dashed">
            <div className="h-px w-12 bg-border md:hidden mb-4" />
            <span className="text-xs font-bold text-muted-foreground px-3 py-1 border rounded-full">VS</span>
            <div className="h-px w-12 bg-border md:hidden mt-4" />
          </div>

          {/* Player 2 */}
          <div className="flex-1 p-8 flex flex-col items-center text-center space-y-4">
            <span className="text-4xl font-black text-primary">{h2h.losses}</span>
            <div className="space-y-1">
              <h2 className="text-2xl font-bold">{opponent.name}</h2>
              <p className="text-sm text-muted-foreground">{opponent.nationality} • {opponent.hand === 'R' ? 'Right' : 'Left'}-handed</p>
            </div>
          </div>
        </div>

        {/* Prediction / Probabilities */}
        {prediction.prediction !== null && (
          <div className="bg-primary/5 border-t p-6">
            <div className="max-w-md mx-auto space-y-4">
              <div className="flex justify-between items-end mb-1">
                <span className="text-sm font-semibold">{player.name}</span>
                <span className="text-2xl font-black">{(prediction.prediction * 100).toFixed(1)}%</span>
                <span className="text-sm font-semibold text-right">{opponent.name}</span>
              </div>
              <div className="h-3 w-full bg-muted rounded-full overflow-hidden flex">
                <div 
                  className="h-full bg-primary transition-all duration-1000" 
                  style={{ width: `${prediction.prediction * 100}%` }} 
                />
                <div 
                  className="h-full bg-muted-foreground/30 transition-all duration-1000" 
                  style={{ width: `${(1 - prediction.prediction) * 100}%` }} 
                />
              </div>
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <span>Win probability based on {matchup.surface === "ALL" ? "overall" : matchup.surface} Elo ratings</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function H2HStatsComparison({ matchup }: { matchup: MatchupDetail }) {
  const { player, opponent } = matchup

  const elo_label = matchup.surface === "ALL" ? "Elo Rating" : `${matchup.surface} Elo Rating`
  const elo_rank_label = matchup.surface === "ALL" ? "Elo Rank" : `${matchup.surface} Elo Rank`
  const form_label = matchup.surface === "ALL" ? "Recent Form" : `${matchup.surface} Form`

  const rows = [
    { label: elo_label, p1: player.elo?.toFixed(0), p2: opponent.elo?.toFixed(0), better: "high" },
    { label: elo_rank_label, p1: player.rank, p2: opponent.rank, better: "low" },
    { 
      label: form_label, 
      p1: player.form.weighted_form != null ? Math.round(player.form.weighted_form * 100) : "N/A", 
      p2: opponent.form.weighted_form != null ? Math.round(opponent.form.weighted_form * 100) : "N/A", 
      better: "high" 
    },
    { label: "Season Wins", p1: player.season_record.won, p2: opponent.season_record.won, better: "high" },
    { label: "Season Win %", p1: (player.season_record.win_pct * 100).toFixed(1) + "%", p2: (opponent.season_record.win_pct * 100).toFixed(1) + "%", better: "high" },
    { label: "Career Wins", p1: player.career_record.won, p2: opponent.career_record.won, better: "high" },
    { label: "Career Win %", p1: (player.career_record.win_pct * 100).toFixed(1) + "%", p2: (opponent.career_record.win_pct * 100).toFixed(1) + "%", better: "high" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          {matchup.surface !== "ALL" ? matchup.surface : ""} Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {rows.map((row, i) => {
            const p1Val = parseFloat(row.p1 as string) || 0
            const p2Val = parseFloat(row.p2 as string) || 0
            const p1Better = row.better === "high" ? p1Val > p2Val : p1Val < p2Val && p1Val !== 0
            const p2Better = row.better === "high" ? p2Val > p1Val : p2Val < p1Val && p2Val !== 0

            return (
              <div key={i} className="flex items-center gap-4 py-3 border-b last:border-0 border-muted/50 transition-colors hover:bg-muted/10 px-2 rounded-md">
                <div className={cn(
                  "flex-1 text-right text-lg tabular-nums transition-colors",
                  p1Better ? "font-bold text-primary" : "font-semibold text-foreground/70"
                )}>
                  {row.p1 || "—"}
                </div>
                <div className="w-32 text-center text-xs text-muted-foreground uppercase font-bold tracking-wider">
                  {row.label}
                </div>
                <div className={cn(
                  "flex-1 text-left text-lg tabular-nums transition-colors",
                  p2Better ? "font-bold text-primary" : "font-semibold text-foreground/70"
                )}>
                  {row.p2 || "—"}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function H2HMatchHistory({ history, p1Id }: { history: Match[], p1Id: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <History className="h-5 w-5" />
          Match History
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="pl-6">Date</TableHead>
              <TableHead>Tournament</TableHead>
              <TableHead>Result</TableHead>
              <TableHead className="text-right pr-6">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {history.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  No matches found between these players.
                </TableCell>
              </TableRow>
            ) : (
              history.map((match) => {
                const p1Won = match.winner_id === p1Id
                return (
                  <TableRow key={match.match_id}>
                    <TableCell className="pl-6 text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(match.match_date).toLocaleDateString(undefined, { 
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </TableCell>
                    <TableCell className="text-sm font-medium">
                      <div className="flex flex-col">
                        <span>{match.tournament_name}</span>
                        <span className="text-[10px] text-muted-foreground uppercase">{match.surface} • {match.round}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold",
                        p1Won ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      )}>
                        {p1Won ? 'P1 WON' : 'P2 WON'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right pr-6 tabular-nums text-sm font-medium">
                      {match.score}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
