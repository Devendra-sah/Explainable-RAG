import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from backend/.env")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rag_answers (
    answer_id BIGSERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES queries(query_id),
    answer_text TEXT NOT NULL,
    model_name VARCHAR(150) NOT NULL,
    prompt_version VARCHAR(30) NOT NULL DEFAULT 'v1',
    generation_latency_ms DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_answer_sources (
    answer_source_id BIGSERIAL PRIMARY KEY,
    answer_id BIGINT NOT NULL
        REFERENCES rag_answers(answer_id) ON DELETE CASCADE,
    chunk_id INTEGER NOT NULL REFERENCES chunks(chunk_id),
    document_id INTEGER NOT NULL REFERENCES documents(document_id),
    source_rank INTEGER NOT NULL,
    citation_label VARCHAR(20) NOT NULL,
    similarity_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (answer_id, chunk_id),
    UNIQUE (answer_id, citation_label)
);

CREATE INDEX IF NOT EXISTS idx_rag_answers_query_id
    ON rag_answers(query_id);

CREATE INDEX IF NOT EXISTS idx_rag_answer_sources_answer_id
    ON rag_answer_sources(answer_id);

CREATE INDEX IF NOT EXISTS idx_rag_answer_sources_chunk_id
    ON rag_answer_sources(chunk_id);
"""

with psycopg.connect(DATABASE_URL) as connection:
    with connection.cursor() as cursor:
        cursor.execute(SCHEMA_SQL)

print("RAG answer and source tables created successfully.")
