
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from backend/.env")

SQL = """
ALTER TABLE rag_answers
    ADD COLUMN IF NOT EXISTS abstained BOOLEAN
        NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_similarity_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS retrieval_threshold DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS citation_valid BOOLEAN
        NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS citation_errors JSONB
        NOT NULL DEFAULT '[]'::jsonb;
"""

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.execute(SQL)

print("RAG validation columns added successfully.")
