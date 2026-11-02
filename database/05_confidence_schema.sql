-- ==========================================================
-- F3: Confidence & Query-Level Explainability
-- ==========================================================

ALTER TABLE explanations
ADD COLUMN IF NOT EXISTS confidence_score
DOUBLE PRECISION;

ALTER TABLE explanations
ADD COLUMN IF NOT EXISTS confidence_level
VARCHAR(20);

ALTER TABLE explanations
ADD CONSTRAINT chk_explanation_confidence_score
CHECK (
    confidence_score IS NULL
    OR (
        confidence_score >= 0
        AND confidence_score <= 1
    )
);

ALTER TABLE explanations
ADD CONSTRAINT chk_explanation_confidence_level
CHECK (
    confidence_level IS NULL
    OR confidence_level IN (
        'HIGH',
        'MEDIUM',
        'LOW'
    )
);