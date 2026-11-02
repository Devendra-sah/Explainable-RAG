-- ============================================================
-- Explainable Vector Database Management Framework for RAG
-- Database Schema
-- PostgreSQL + pgvector
-- ============================================================

-- ------------------------------------------------------------
-- 1. Enable pgvector
-- ------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================
-- 2. DOCUMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS documents (
    document_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    file_name VARCHAR(255) NOT NULL,

    file_type VARCHAR(20) NOT NULL,

    author VARCHAR(255),

    subject VARCHAR(255),

    file_hash VARCHAR(64) UNIQUE,

    file_size_bytes BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_document_file_type
        CHECK (file_type IN ('pdf', 'txt', 'docx'))
);


-- ============================================================
-- 3. CHUNKS
-- ============================================================

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    document_id BIGINT NOT NULL,

    chunk_text TEXT NOT NULL,

    chunk_index INTEGER NOT NULL,

    page_number INTEGER,

    token_count INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chunk_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_chunk_index
        CHECK (chunk_index >= 0),

    CONSTRAINT chk_chunk_page
        CHECK (page_number IS NULL OR page_number > 0),

    CONSTRAINT chk_chunk_token_count
        CHECK (token_count IS NULL OR token_count >= 0),

    CONSTRAINT uq_document_chunk_index
        UNIQUE (document_id, chunk_index)
);


-- ============================================================
-- 4. EMBEDDINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    chunk_id BIGINT NOT NULL UNIQUE,

    model_name VARCHAR(255) NOT NULL,

    dimension INTEGER NOT NULL,

    embedding VECTOR(384) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_embedding_chunk
        FOREIGN KEY (chunk_id)
        REFERENCES chunks(chunk_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_embedding_dimension
        CHECK (dimension = 384)
);


-- ============================================================
-- 5. QUERIES
-- ============================================================

CREATE TABLE IF NOT EXISTS queries (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    query_text TEXT NOT NULL,

    top_k INTEGER NOT NULL DEFAULT 5,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_query_top_k
        CHECK (top_k > 0)
);


-- ============================================================
-- 6. RETRIEVAL RESULTS
-- ============================================================

CREATE TABLE IF NOT EXISTS retrieval_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    query_id BIGINT NOT NULL,

    chunk_id BIGINT NOT NULL,

    rank INTEGER NOT NULL,

    similarity_score DOUBLE PRECISION NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_result_query
        FOREIGN KEY (query_id)
        REFERENCES queries(query_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_result_chunk
        FOREIGN KEY (chunk_id)
        REFERENCES chunks(chunk_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_result_rank
        CHECK (rank > 0),

    CONSTRAINT chk_similarity_score
        CHECK (
            similarity_score >= -1.0
            AND similarity_score <= 1.0
        ),

    CONSTRAINT uq_query_chunk
        UNIQUE (query_id, chunk_id),

    CONSTRAINT uq_query_rank
        UNIQUE (query_id, rank)
);


-- ============================================================
-- 7. EXPLANATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS explanations (
    explanation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    result_id BIGINT NOT NULL UNIQUE,

    semantic_score DOUBLE PRECISION,

    keyword_score DOUBLE PRECISION,

    metadata_score DOUBLE PRECISION,

    ranking_score DOUBLE PRECISION,

    explainability_score DOUBLE PRECISION,

    explanation_text TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_explanation_result
        FOREIGN KEY (result_id)
        REFERENCES retrieval_results(result_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_semantic_score
        CHECK (
            semantic_score IS NULL
            OR semantic_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_keyword_score
        CHECK (
            keyword_score IS NULL
            OR keyword_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_metadata_score
        CHECK (
            metadata_score IS NULL
            OR metadata_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_ranking_score
        CHECK (
            ranking_score IS NULL
            OR ranking_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_explainability_score
        CHECK (
            explainability_score IS NULL
            OR explainability_score BETWEEN 0 AND 1
        )
);


-- ============================================================
-- 8. RETRIEVAL LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS retrieval_logs (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    query_id BIGINT NOT NULL UNIQUE,

    embedding_time_ms DOUBLE PRECISION,

    retrieval_time_ms DOUBLE PRECISION,

    explanation_time_ms DOUBLE PRECISION,

    total_latency_ms DOUBLE PRECISION,

    candidate_count INTEGER,

    result_count INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_query
        FOREIGN KEY (query_id)
        REFERENCES queries(query_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_embedding_time
        CHECK (
            embedding_time_ms IS NULL
            OR embedding_time_ms >= 0
        ),

    CONSTRAINT chk_retrieval_time
        CHECK (
            retrieval_time_ms IS NULL
            OR retrieval_time_ms >= 0
        ),

    CONSTRAINT chk_explanation_time
        CHECK (
            explanation_time_ms IS NULL
            OR explanation_time_ms >= 0
        ),

    CONSTRAINT chk_total_latency
        CHECK (
            total_latency_ms IS NULL
            OR total_latency_ms >= 0
        ),

    CONSTRAINT chk_candidate_count
        CHECK (
            candidate_count IS NULL
            OR candidate_count >= 0
        ),

    CONSTRAINT chk_result_count
        CHECK (
            result_count IS NULL
            OR result_count >= 0
        )
);