CREATE TABLE IF NOT EXISTS explanation_evidence (

    evidence_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    explanation_id BIGINT NOT NULL,

    evidence_type VARCHAR(50) NOT NULL,

    evidence_text TEXT NOT NULL,

    contribution_score DOUBLE PRECISION,

    evidence_rank INTEGER NOT NULL,

    created_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_evidence_explanation
        FOREIGN KEY (explanation_id)
        REFERENCES explanations(explanation_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_evidence_contribution
        CHECK (
            contribution_score IS NULL
            OR (
                contribution_score >= 0
                AND contribution_score <= 1
            )
        ),

    CONSTRAINT chk_evidence_rank
        CHECK (evidence_rank > 0)
);