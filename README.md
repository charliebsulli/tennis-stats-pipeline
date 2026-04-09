# ATP Tennis Analytics Pipeline

A data pipeline and REST API for ATP tennis statistics, ELO rankings, and derived analytics.

**Live API:** [https://tennis-stats-pipeline-production.up.railway.app/docs/](https://tennis-stats-pipeline-production.up.railway.app/docs/)

## Overview

This project is a data pipeline and REST API for tennis analytics. It ingests match data from a historical CSV dataset and a live tennis API, reconciling them into a PostgreSQL database covering 400K+ matches across 50+ years. 

The pipeline stores raw data from both sources before extracting players, tournaments, matches, and per-player match statistics into normalized tables. Because the two sources use incompatible player ID systems, fuzzy matching is used to resolve player identities across the sources, ensuring accurate statistics and a uniform match history for each player. Player statistics are then aggregated by surface and season, head-to-head records computed, and Elo rankings calculated across the full match history. 

New match data is ingested and processed daily, keeping all statistics and ratings up-to-date.

A live API exposes these derived statistics:

- Serve and return stats for any combination of player, surface and season
- Surface specific Elo rankings at any point in history since 1968
- Complete Elo rating history for any player across their career
- Form scores for each player, derived from their recent results
- Head to head records and detailed matchup profiles for any pair of players
- Elo-based win probability predictions (achieving 63.8% accuracy on 2024 match data)

## Architecture

```
Sources: Historical CSVs (1968-2024) + RapidAPI (2024–present)
       ↓
Ingestion Layer (daily scheduled job)
       ↓
Raw Layer — PostgreSQL (source data as-is)
       ↓
Transform Layer (normalize, clean, resolve player IDs)
       ↓
Analytics Layer — matches, players, tournaments, match_stats
       ↓
Aggregate Layer — ELO history, form scores, H2H records, surface stats
       ↓
REST API (FastAPI)
```

## Engineering Decisions

### Schema

Raw match data from both sources is stored in a staging table before transformation. This provides a way of debugging data quality issues in downstream tables and simplifies reconciliation between the two sources, since both are preserved in their original form.

### Player ID Resolution

Players from the API must be linked to the corresponding players in the historical dataset to avoid duplicate players and ensure accurate statistics, continuous match history, and correct Elo rating history for each player. Since the CSV data and API use different systems for player IDs, players' names are used to match player IDs from the API to player IDs in the historical data. There are some differences in how names are formatted, so names are normalized to remove hypens, accents, and capitalization before being fuzzy matched to names which are already in the players table (which uses the ID from the historical dataset as the canonical player ID). Once matched, the API player ID and canonical player ID are stored in a crosswalk table, making all subsequent lookups O(1) rather than repeating the fuzzy match on every pipeline run.

### Incremental Ingestion

When new data is ingested, it is important to avoid duplicate records and only recompute stats which need to be updated in order to maintain data integrity and pipeline efficiency. The pipeline is designed to be safely re-runnable at any time without producing duplicate records or redundant computation:

- Match data ingested from the API is only inserted into the raw data table when the API match ID is not already present
- The transform step only processes matches from the raw table whose match ID is not in the normalized matches table, and only new players and tournaments are added
- Per-player stats records are marked with a timestamp and are only updated if new matches for that player have been ingested since the record was last updated
- Elo ratings are recomputed from the oldest of the matches ingested in any pipeline run: if data is missing for a day and ingested later, Elo ratings will account for that

### Surface Elo

Surface-specific Elo ratings are used to rank players since player performance differs meaningfully between surfaces. Each variation of the Elo algorithm was run from the earliest match (1968), with 2023 used as a validation set and 2024 as a held-out test set. The highest match prediction accuracy used the following configuration:

- Players start at 1500 Elo
- k-factor is a constant 32
- Completely separate Elo ratings are kept per-surface, but averaged (50/50) with overall ratings to rank players and predict match outcomes

Surface-specific ratings are averaged with overall ratings (computed across all matches) since a strong correlation is expected between overall Elo and performance on each surface. When only surface-specific ratings are used on that surface, prediction accuracy drops significantly. Here are the results on the 2023 data: the first row of each table uses overall rankings to predict every match in that year, and the rest of the rows use surface-specific ratings.

**Without averaging:**

- Surface-specific predictions are made only using surface-specific elo ratings


| Surface | Total  | Correct | Accuracy |
| ------- | ------ | ------- | -------- |
| ALL     | 13,649 | 8,678   | 63.6%    |
| Hard    | 6,964  | 4,382   | 62.9%    |
| Clay    | 5,912  | 3,727   | 63.0%    |
| Grass   | 671    | 391     | 58.3%    |


**With averaging:**

- 50/50 average between a player's overall and surface-specific rating at the time of prediction


| Surface | Total  | Correct | Accuracy |
| ------- | ------ | ------- | -------- |
| ALL     | 13,649 | 8,681   | 63.6%    |
| Hard    | 6,964  | 4,429   | 63.6%    |
| Clay    | 5,912  | 3,765   | 63.7%    |
| Grass   | 671    | 441     | 65.7%    |


The most notable improvment is on grass, where accuracy jumped from 58.3% to 65.7%. Grass ratings are computed over a smaller sample, so they are far less accurate without averaging. The strength of the overall rankings when predicting across all surfaces (63.6%) indicates strong correlation betwen overall rating and match outcomes.

## API

| Endpoint | Description |
|---|---|
| `GET /players/search?name=` | Search for players by name |
| `GET /players/{id}` | Get profile information for a player by ID |
| `GET /players/{id}/stats?surface=&season=` | Retrieve detailed serve and return stats for a player |
| `GET /players/{id}/elo?surface=` | Returns the latest Elo rating and rank for a player |
| `GET /players/{id}/elo/history?surface=` | Get the historical Elo rating progression for a player |
| `GET /players/{id}/form?surface=` | Retrieve current performance form metrics for a player |
| `GET /players/{id}/matches?surface=&limit=` | Retrieve a list of recent matches for a specific player |
| `GET /matchups/h2h?player_id=&opponent_id=&surface=` | Get the head-to-head win/loss record between two players |
| `GET /matchups/prediction?player_id=&opponent_id=&surface=` | Predict win probability for a matchup based on current Elo |
| `GET /matchups/detailed?player_id=&opponent_id=&surface=` | Detailed side-by-side comparison and match history for two players |
| `GET /rankings?surface=&date=` | Retrieve the top Elo-ranked players for a specific surface and date |
| `GET /matches/recent?limit=` | Retrieve the most recently completed matches |
| `GET /matches/{id}` | Retrieve details for a specific match by ID |

## Derived Stats

- Detailed serve and return statistics are available from 1991 onwards, when detailed stats collection started
- Elo rating history uses the standard Elo rules for computing expectation and updating Elo, and rating computation begins in 1968
- Weighted form uses only data from the last 90 days, and daily exponential decay with alpha = 0.97 to weight recent matches more highly

## Tech Stack

- **Pipeline:** Python, Pandas, SQLAlchemy, rapidfuzz
- **Database:** PostgreSQL
- **API:** FastAPI, Pydantic
- **Infrastructure:** Railway (API + DB + cron), GitHub Actions (CI)
- **Data sources:** Jeff Sackmann's tennis_atp dataset, RapidAPI Tennis API

## Running locally

1. Clone the repo and install dependencies

```bash
git clone https://github.com/charliebsulli/tennis-stats-pipeline.git
cd tennis-stats-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Get the historical dataset and set environment variables

- Clone Jeff Sackmann's [ATP Tennis dataset](https://github.com/JeffSackmann/tennis_atp) and point `DATASET_PATH` to the folder containing the CSV files
- Obtain an API key for the [tennis API](https://rapidapi.com/fluis.lacasse/api/tennisapi1) from RapidAPI and set `API_KEY`
- Set `DB_CONNECTION_STR` to your PostgreSQL database

```
DATASET_PATH=
API_KEY=
DB_CONNECTION_STR=
```

3. Run scripts

Run all scripts from the root directory to ensure imports work as expected.

First, run `seed.py` to create the DB tables and load the historical dataset.

```bash
python -m pipeline.seed
```

Then, `backfill.py` loads data from the end of 2024 until today. This will hit the API limit very quickly on the free plan. Finally, running `pipeline.py` will ingest yesterday's match data, transform and normalize it, and update statistics, Elo ratings, and form scores.

```bash
python -m pipeline.backfill

python -m pipeline.pipeline
```

Both `backfill` and `pipeline` can take dates as command line arguments to load data from a specific date range (for `backfill`) or a specific date (for `pipeline`).

4. Start the FastAPI server to try the endpoints

```bash
fastapi dev api/main.py
# OR
uvicorn api.main:app
```

## Data Sources

Historical match data from [Jeff Sackmann's tennis_atp dataset](https://github.com/JeffSackmann/tennis_atp). In accordance with the license, this project is for non-commercial use only.

Live match data from [RapidAPI Tennis API](https://rapidapi.com/fluis.lacasse/api/tennisapi1).

