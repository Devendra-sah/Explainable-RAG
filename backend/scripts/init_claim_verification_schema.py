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
    ADD COLUMN IF NOT EXISTS generated_answer_text TEXT,
    ADD COLUMN IF NOT EXISTS grounding_valid BOOLEAN,
    ADD COLUMN IF NOT EXISTS grounding_status VARCHAR(30)
        NOT NULL DEFAULT 'not_checked',
    ADD COLUMN IF NOT EXISTS grounding_errors JSONB
        NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS rag_claim_verifications (
    claim_verification_id BIGSERIAL PRIMARY KEY,
    answer_id BIGINT NOT NULL
        REFERENCES rag_answers(answer_id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    verdict VARCHAR(20) NOT NULL,
    citation_labels JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_quote TEXT,
    evidence_quote_valid BOOLEAN NOT NULL DEFAULT FALSE,
    verification_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        verdict IN (
            'supported',
            'unsupported',
            'insufficient',
            'unverified'
        )
    )
);

ALTER TABLE rag_claim_verifications
    DROP CONSTRAINT IF EXISTS rag_claim_verifications_verdict_check;

ALTER TABLE rag_claim_verifications
    ADD CONSTRAINT rag_claim_verifications_verdict_check
    CHECK (
        verdict IN (
            'supported',
            'unsupported',
            'insufficient',
            'unverified'
        )
    );

CREATE INDEX IF NOT EXISTS idx_claim_verifications_answer_id
    ON rag_claim_verifications(answer_id);

CREATE INDEX IF NOT EXISTS idx_claim_verifications_verdict
    ON rag_claim_verifications(verdict);
"""

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.execute(SQL)

print("Claim-verification schema created successfully.")
