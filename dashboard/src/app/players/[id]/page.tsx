export default function PlayerProfile({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Player Profile: {params.id}</h1>
      <p className="mt-4 text-gray-600">This page will display player statistics, ELO history, and recent matches.</p>
    </div>
  );
}
