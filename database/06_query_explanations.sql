-- ==========================================================
-- F3: Query-Level Explainability
-- ==========================================================

CREATE TABLE IF NOT EXISTS query_explanations (

    query_explanation_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    query_id BIGINT NOT NULL UNIQUE,

    overall_confidence_score
        DOUBLE PRECISION NOT NULL,

    confidence_level
        VARCHAR(20) NOT NULL,

    result_count
        INTEGER NOT NULL,

    top_similarity
        DOUBLE PRECISION NOT NULL,

    second_similarity
        DOUBLE PRECISION,

    similarity_margin
        DOUBLE PRECISION,

    average_similarity
        DOUBLE PRECISION NOT NULL,

    average_explainability
        DOUBLE PRECISION NOT NULL,

    explanation_text
        TEXT NOT NULL,

    created_at
        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_query_explanation_query
        FOREIGN KEY (query_id)
        REFERENCES queries(query_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_query_confidence_score
        CHECK (
            overall_confidence_score >= 0
            AND overall_confidence_score <= 1
        ),

    CONSTRAINT chk_query_confidence_level
        CHECK (
            confidence_level IN (
                'HIGH',
                'MEDIUM',
                'LOW'
            )
        ),

    CONSTRAINT chk_query_result_count
        CHECK (result_count > 0),

    CONSTRAINT chk_query_top_similarity
        CHECK (
            top_similarity >= -1
            AND top_similarity <= 1
        ),

    CONSTRAINT chk_query_second_similarity
        CHECK (
            second_similarity IS NULL
            OR (
                second_similarity >= -1
                AND second_similarity <= 1
            )
        ),

    CONSTRAINT chk_query_margin
        CHECK (
            similarity_margin IS NULL
            OR similarity_margin >= 0
        ),

    CONSTRAINT chk_query_average_similarity
        CHECK (
            average_similarity >= -1
            AND average_similarity <= 1
        ),

    CONSTRAINT chk_query_average_explainability
        CHECK (
            average_explainability >= 0
            AND average_explainability <= 1
        )
);