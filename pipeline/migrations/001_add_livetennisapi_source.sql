-- Adds the optional Live Tennis API source.
--
-- schema.sql is only applied to a fresh database by seed.py, so an existing
-- database needs this applied by hand:
--     psql "$DB_CONNECTION_STR" -f pipeline/migrations/001_add_livetennisapi_source.sql
--
-- Safe to run on a populated database: every change is additive and the
-- existing rows keep working. Only needed if you actually set
-- LIVETENNISAPI_KEY.

BEGIN;

-- 1. Live Tennis API ids, kept in their own namespace so they can never be
--    confused with RapidAPI or Sackmann ids.
ALTER TABLE raw_matches ADD COLUMN IF NOT EXISTS ltapi_match_id INTEGER;
ALTER TABLE raw_matches ADD COLUMN IF NOT EXISTS ltapi_winner_id INTEGER;
ALTER TABLE raw_matches ADD COLUMN IF NOT EXISTS ltapi_loser_id INTEGER;

-- The ingest dedupes with ON CONFLICT (ltapi_match_id), which needs a unique
-- constraint. NULLs do not conflict, so existing rows are unaffected.
ALTER TABLE raw_matches
    ADD CONSTRAINT raw_matches_ltapi_match_id_key UNIQUE (ltapi_match_id);

-- 2. An API player id is only meaningful together with the API it came from:
--    two providers can hand out the same integer for different people.
--    Existing rows all came from RapidAPI, which is what the default records.
ALTER TABLE player_id_lookup
    ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'rapidapi';

ALTER TABLE player_id_lookup DROP CONSTRAINT player_id_lookup_pkey;
ALTER TABLE player_id_lookup
    ADD PRIMARY KEY (player_id, api_player_id, source);

COMMIT;
