CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS captions (
    id BIGSERIAL PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    start_time DOUBLE PRECISION NOT NULL,
    duration DOUBLE PRECISION NOT NULL
);

-- Generated tsvector column for efficient Danish full-text search.
ALTER TABLE captions
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('danish', coalesce(text, ''))) STORED;

CREATE INDEX IF NOT EXISTS idx_captions_video_id ON captions(video_id);
CREATE INDEX IF NOT EXISTS idx_captions_search_vector ON captions USING GIN(search_vector);
