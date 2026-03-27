CREATE TABLE player_form (
  matches_total INTEGER NOT NULL,
  won INTEGER not null,
  player_id INTEGER REFERENCES players(player_id),
  surface TEXT not null,
  last_updated timestamptz not null,
  weighted_form real
)

ALTER TABLE matches ADD COLUMN round_int INTEGER;