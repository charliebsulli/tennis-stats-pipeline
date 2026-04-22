import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Player, EloResponse, PlayerForm } from "@/types/api"

interface PlayerHeaderProps {
  player: Player
  elo?: EloResponse
  form?: PlayerForm
  eloLoading?: boolean
  formLoading?: boolean
  eloError?: any
  formError?: any
}

export function PlayerHeader({
  player,
  elo,
  form,
  eloLoading,
  formLoading,
  eloError,
  formError,
}: PlayerHeaderProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="mb-4 text-3xl">{player.name}</CardTitle>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {eloLoading ? (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </>
          ) : eloError ? (
            <div className="col-span-2 rounded-lg border border-red-100 bg-muted p-3 text-center">
              <p className="text-sm text-red-500">Elo unavailable</p>
            </div>
          ) : (
            <>
              <div className="rounded-lg bg-muted p-3 text-center">
                <p className="text-2xl font-medium">#{elo?.rank}</p>
                <p className="mt-1 text-xs text-muted-foreground">ELO Rank</p>
              </div>
              <div className="rounded-lg bg-muted p-3 text-center">
                <p className="text-2xl font-medium">
                  {Math.round(elo?.elo ?? 0)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">ELO Rating</p>
              </div>
            </>
          )}

          {formLoading ? (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </>
          ) : formError ? (
            <div className="col-span-2 rounded-lg border border-red-100 bg-muted p-3 text-center">
              <p className="text-sm text-red-500">Form unavailable</p>
            </div>
          ) : (
            <>
              <div className="rounded-lg bg-muted p-3 text-center">
                <p className="text-2xl font-medium">
                  {Math.round((form?.weighted_form ?? 0) * 100)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">Form Score</p>
              </div>
              <div className="rounded-lg bg-muted p-3 text-center">
                <p className="text-2xl font-medium">
                  {form?.won}-{ (form?.matches_total ?? 0) - (form?.won ?? 0) }
                </p>
                <p className="mt-1 text-xs text-muted-foreground">W-L (90d)</p>
              </div>
            </>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <Separator className="mb-4" />
        <dl className="flex gap-8">
          <div>
            <dt className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Nationality</dt>
            <dd className="mt-1 text-base font-medium">{player.nationality || "Unknown"}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Plays</dt>
            <dd className="mt-1 text-base font-medium">
              {player.hand === "R"
                ? "Right-handed"
                : player.hand === "L"
                ? "Left-handed"
                : "Unknown"}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  )
}
