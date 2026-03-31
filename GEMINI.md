# Tennis Analytics Pipeline

## Project Overview
A multi-layer ETL pipeline that ingests ATP tennis match data from two sources 
(Jeff Sackmann's historical CSV dataset and a RapidAPI tennis API), transforms 
and normalizes it into a PostgreSQL analytics database, and computes derived 
statistics including player surface splits, head-to-head records, form ratings, 
and surface-specific ELO ratings.

This is a portfolio project targeting backend SWE and data engineering roles. 
The pipeline will eventually be paired with a FastAPI REST API and a React frontend.

## Architecture
```
Sources: Sackmann CSVs (historical, up to 2024) + RapidAPI (live, 2024-present)
       ↓
Ingestion Layer: seed.py (one-time historical load) + ingest.py (daily cron)
       ↓
Raw Layer: raw_matches table (source data stored as-is, with pipeline metadata)
       ↓
Transform Layer: transform.py (normalize, clean, resolve player IDs)
       ↓
Analytics Layer: matches, players, tournaments, match_stats tables
       ↓
Aggregate Layer: player_surface_stats, head_to_head, player_form, elo_history
       ↓
(Upcoming) REST API: FastAPI
(Upcoming) Frontend: React
```

## Tech Stack
- **Language:** Python
- **Database:** PostgreSQL (SQLite for local dev fallback)
- **ORM / Query:** SQLAlchemy 2.0 with raw SQL via `text()`
- **Data processing:** Pandas
- **Fuzzy matching:** rapidfuzz (for cross-source player ID resolution)
- **Schema management:** Single `schema.sql` file, applied via `db/migrate.py`
- **API source:** RapidAPI tennis API
- **Historical data:** Jeff Sackmann's tennis_atp GitHub dataset

## Key Design Decisions

### Two-layer schema
Raw data is stored exactly as received from the source before any transformation.
This allows pipeline reruns without data loss and makes debugging source data 
issues possible. The analytics layer contains cleaned, normalized, renamed data.

### Player ID crosswalk
Sackmann CSVs and the RapidAPI use different player ID systems. A `player_id_lookup`
table maps API player IDs to canonical internal IDs using fuzzy name matching 
(rapidfuzz) during an initial seeding step. All subsequent lookups are O(1) 
table lookups, not fuzzy matches.

### Long format match stats
Match stats are stored one row per player per match (not one row per match with 
winner/loser columns). This makes player-centric queries simple and eliminates 
the need for conditional column selection based on which side of the match a 
player was on.

### Incremental ingestion
Both ingestion and transformation are incremental — they only process records 
not already present in the target table. This makes all pipeline scripts safe 
to re-run at any time without duplicating data.

### Surface-specific ELO
ELO ratings are maintained separately per surface (Hard, Clay, Grass, ALL) 
since surface specialization is a defining characteristic of tennis performance.
Each match updates both the surface-specific and overall ratings.

### ELO rollback on late data
When new matches predate the current ELO state (e.g. during backfill or late 
API reporting), the pipeline deletes ELO history from the earliest new match 
date forward and recomputes from that point to maintain correctness.

## Database Schema Summary
- `raw_matches` — source data as ingested, one row per match per source
- `players` — canonical player records with generated IDs
- `tournaments` — tournament metadata including surface and tier
- `matches` — normalized match results with round ordering
- `match_stats` — per-player per-match statistics (long format)
- `player_id_lookup` — crosswalk between API IDs and internal player IDs
- `player_surface_stats` — pre-computed aggregates by player/surface/season
- `head_to_head` — win/loss records between player pairs by surface
- `player_form` — time-decayed weighted form score by player/surface
- `elo_history` — full ELO rating history per player per match per surface

## Environment Variables
- `DB_CONNECTION_STR` — PostgreSQL connection string
- `API_KEY` — API key for the tennis data API
- `DATASET_PATH` — path to local Sackmann CSV files (used by seed.py only)

## Running the Pipeline
```bash
# first time setup
python seed.py             # load historical CSV data
python backfill.py          # load historical data from api, starting end of 2024
# daily pipeline
python pipeline.py         # ingest → transform → aggregate → ELO
```

## Known Limitations / Future Work
- Futures tournaments excluded due to data quality
- Frontend and API layer not yet built