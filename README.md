# ATP Tennis Analytics Pipeline

A data pipeline and REST API for ATP tennis statistics, ELO rankings, and derived analytics. # fix the last part starting at tennis

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

## Engineering Decisions

### Schema

All of the raw match data is stored in the database before transforming it into normalized match, player, and tournament data. This makes it easier to identify the source of errors in the transformed tables, whose records are linked by match ID to the raw data. It also eases the process of normalizing and reconciling the differences between the two data sources, since a large number of records from each source are saved. Without storing the raw data, identifying the source of errors in data sourced from the API would be more difficult, since that data would have to be fetched again for analysis.


### Player ID Resolution

Players from the API must be linked to the corresponding players in the historical dataset to avoid duplicate players and ensure accurate statistics, continuous match history, and correct Elo rating history for each player. Since the CSV data and API use different systems for player IDs, players' names are used to match player IDs from the API to player IDs in the historical data. Since there are some differences in how names are formatted, names are normalized to remove hypens, accents, and capitalization before being fuzzy matched to names which are already in the players table (which uses the ID from the historical dataset as the canonical player ID). Once a match is made, the API player ID and CSV player ID are stored in a lookup table to avoid repeated fuzzy matching.

### Incremental Ingestion

When new data is ingested, it is important to avoid duplicate records and only recompute stats which need to be updated in order to maintain data integrity and pipeline efficiency. Here is how repeated runs of the pipeline are made safe from errors:
- Match data ingested from the API is only inserted into the raw data table when the API match ID is not already present
- The transform step only processes matches from the raw table whose match ID is not in the normalized matches table, and only new players and tournaments are added
- Per-player stats records are marked with a timestamp and are only updated if new matches for that player have been ingested since the the record was last updated
- Elo ratings are recomputed from the oldest of the matches ingested in any pipeline run: if data is missing for a day and ingested later, Elo ratings will account for that

### Surface Elo

Surface-specific Elo ratings are used to rank players since player performance differs meaningfully between surfaces. Each variation of the Elo algorithm was run from the earliest match (1968), with 2023 used as a dev set and 2024 as a held-out test set. The highest match prediction accuracy used the following configuration:
- Players start at 1500 Elo
- k-factor is a constant 32
- Completely separate Elo ratings are kept per-surface, but averaged (50/50) with overall ratings to rank players and predict match outcomes

Surface-specific ratings are averaged with overall ratings since a strong correlation is expected between overall Elo and performance on each surface. When only surface-specific ratings are used on that surface, prediction accuracy drops significantly.

## API endpoints

- table of endpoints w/ descriptions

## Derived stats

- explain the more interesting stats my dataset computes

## Tech Stack

- **Pipeline:** Python, Pandas, SQLAlchemy, rapidfuzz
- **Database:** PostgreSQL
- **API:** FastAPI, Pydantic
- **Infrastructure:** Railway (API + DB + cron), GitHub Actions (CI)
- **Data sources:** Jeff Sackmann's tennis_atp dataset, RapidAPI Tennis API

## Running locally

- how to run locally, try this clean once I've written the steps

## Data source attribution

