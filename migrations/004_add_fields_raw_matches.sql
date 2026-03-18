-- fields for ingesting rapidapi match data
ALTER TABLE raw_matches ADD COLUMN rapidapi_match_id INTEGER;
ALTER TABLE raw_matches ADD COLUMN rapidapi_tournament_id INTEGER;
ALTER TABLE raw_matches ADD COLUMN rapidapi_winner_id INTEGER;
ALTER TABLE raw_matches ADD COLUMN rapidapi_loser_id INTEGER;
-- sackmann only has tournament date, match_date is a timestamp of match start time
ALTER TABLE raw_matches ADD COLUMN match_date INTEGER;