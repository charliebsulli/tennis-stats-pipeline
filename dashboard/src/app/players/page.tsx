import { PlayerSearch } from "@/components/player-search";

export default function Players() {
  return (
    <div className="flex flex-col gap-8 py-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Players</h1>
        <p className="text-muted-foreground mt-2">
          Search for players and view their profile with stats and recent results.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">Find a player</h2>
        <PlayerSearch />
      </div>
    </div>
  );
}
