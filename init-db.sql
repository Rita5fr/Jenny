-- Initialize Jenny database with required extensions
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database metadata
COMMENT ON DATABASE jenny_db IS 'Jenny AI Assistant Database - Local PostgreSQL with pgvector';

-- Grant all privileges to jenny user
GRANT ALL PRIVILEGES ON DATABASE jenny_db TO jenny;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Jenny database initialized successfully with pgvector extension';
END $$;
