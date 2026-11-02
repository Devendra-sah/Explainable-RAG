import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.services.embedding_service import EmbeddingService


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")


# --------------------------------------------------
# Database connection
# --------------------------------------------------

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# Embedding service
# --------------------------------------------------

embedding_service = EmbeddingService()


# --------------------------------------------------
# User query
# --------------------------------------------------

query_text = "What is database normalization?"
top_k = 5

print("\nUser Query:")
print(query_text)


# --------------------------------------------------
# Generate query embedding
# --------------------------------------------------

query_embedding = embedding_service.generate_embedding(query_text)

print("\nQuery embedding dimension:")
print(len(query_embedding))

query_vector = str(query_embedding)


# --------------------------------------------------
# Database transaction
# --------------------------------------------------

try:

    with engine.begin() as connection:

        # ==================================================
        # 1. Store the query
        # ==================================================

        query_result = connection.execute(
            text("""
                INSERT INTO queries
                    (query_text, top_k)
                VALUES
                    (:query_text, :top_k)
                RETURNING query_id
            """),
            {
                "query_text": query_text,
                "top_k": top_k
            }
        )

        query_id = query_result.scalar_one()

        print("\nQuery stored successfully.")
        print("Query ID:", query_id)


        # ==================================================
        # 2. Perform semantic retrieval
        # ==================================================

        result = connection.execute(
            text("""
                SELECT
                    c.chunk_id,
                    c.chunk_text,
                    d.document_id,
                    d.title,

                    1 - (
                        e.embedding <=> CAST(:query_vector AS vector)
                    ) AS similarity_score

                FROM embeddings e

                JOIN chunks c
                    ON e.chunk_id = c.chunk_id

                JOIN documents d
                    ON c.document_id = d.document_id

                ORDER BY
                    e.embedding <=> CAST(:query_vector AS vector)

                LIMIT :top_k
            """),
            {
                "query_vector": query_vector,
                "top_k": top_k
            }
        )

        rows = result.fetchall()


        # ==================================================
        # 3. Store retrieval results
        # ==================================================

        print("\nSemantic Search Results:")
        print("=" * 70)

        for rank, row in enumerate(rows, start=1):

            similarity_score = float(row.similarity_score)

            connection.execute(
                text("""
                    INSERT INTO retrieval_results
                        (
                            query_id,
                            chunk_id,
                            rank,
                            similarity_score
                        )
                    VALUES
                        (
                            :query_id,
                            :chunk_id,
                            :rank,
                            :similarity_score
                        )
                """),
                {
                    "query_id": query_id,
                    "chunk_id": row.chunk_id,
                    "rank": rank,
                    "similarity_score": similarity_score
                }
            )

            print(f"\nRank: {rank}")
            print(f"Chunk ID: {row.chunk_id}")
            print(f"Document ID: {row.document_id}")
            print(f"Document: {row.title}")
            print(f"Similarity Score: {similarity_score:.4f}")

            print("\nChunk:")
            print(row.chunk_text)

            print("-" * 70)


        print("\nRetrieval results stored successfully.")

        print("Query ID:", query_id)
        print("Results stored:", len(rows))


finally:

    engine.dispose()