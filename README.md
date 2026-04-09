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

## Key engineering decisions

### Schema

### Player ID resolution (or more generally, reconciliation of the two data sources)

### Incremental ingestion

- what am i doing to make sure integrity of the data is preserved as new data is added
- how am I updating the stats to be more efficient than just recomputing, and ensure they stay up to date

### Surface ELO

- explain how I designed the ELO system and why there are two sets of surface ratings

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

