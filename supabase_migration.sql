-- Run this in your Supabase SQL editor to create the ideas table

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS ideas (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  TEXT NOT NULL,
    domain      TEXT NOT NULL,
    app_type    TEXT NOT NULL,
    constraints TEXT,
    ideas       JSONB NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup by session
CREATE INDEX IF NOT EXISTS idx_ideas_session_id ON ideas(session_id);
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at DESC);
