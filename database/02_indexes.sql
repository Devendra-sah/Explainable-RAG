-- ============================================================
-- Explainable Vector Database Management Framework
-- Database Indexes
-- PostgreSQL + pgvector
-- ============================================================


-- ============================================================
-- DOCUMENT INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_documents_subject
ON documents(subject);


CREATE INDEX IF NOT EXISTS idx_documents_file_type
ON documents(file_type);


CREATE INDEX IF NOT EXISTS idx_documents_created_at
ON documents(created_at);


-- ============================================================
-- CHUNK INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON chunks(document_id);


CREATE INDEX IF NOT EXISTS idx_chunks_page_number
ON chunks(page_number);


-- ============================================================
-- EMBEDDING VECTOR INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw
ON embeddings
USING hnsw (embedding vector_cosine_ops);


-- ============================================================
-- QUERY INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_queries_created_at
ON queries(created_at);


-- ============================================================
-- RETRIEVAL RESULT INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_results_query_id
ON retrieval_results(query_id);


CREATE INDEX IF NOT EXISTS idx_results_chunk_id
ON retrieval_results(chunk_id);


CREATE INDEX IF NOT EXISTS idx_results_similarity
ON retrieval_results(similarity_score DESC);


-- ============================================================
-- RETRIEVAL LOG INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_logs_created_at
ON retrieval_logs(created_at);