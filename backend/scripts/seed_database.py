import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.services.embedding_service import EmbeddingService

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)

embedding_service = EmbeddingService()

document_title = "Database Normalization"
file_name = "normalization.txt"
file_type = "txt"

chunk_text = """
Database normalization is a database design technique
used to reduce data redundancy and improve data integrity.
It organizes data into multiple related tables and uses
relationships between those tables to avoid unnecessary duplication.
"""

print("\nGenerating embedding...")
embedding = embedding_service.generate_embedding(chunk_text)

print("Embedding dimension:", len(embedding))

try:
    with engine.begin() as connection:

        # 1. Insert document
        document_result = connection.execute(
            text("""
                INSERT INTO documents
                    (title, file_name, file_type)
                VALUES
                    (:title, :file_name, :file_type)
                RETURNING document_id
            """),
            {
                "title": document_title,
                "file_name": file_name,
                "file_type": file_type
            }
        )

        document_id = document_result.scalar_one()

        # 2. Insert chunk
        chunk_result = connection.execute(
            text("""
                INSERT INTO chunks
                    (document_id, chunk_text, chunk_index)
                VALUES
                    (:document_id, :chunk_text, :chunk_index)
                RETURNING chunk_id
            """),
            {
                "document_id": document_id,
                "chunk_text": chunk_text,
                "chunk_index": 0
            }
        )

        chunk_id = chunk_result.scalar_one()

        # 3. Insert embedding
        connection.execute(
            text("""
                INSERT INTO embeddings
                    (chunk_id, model_name, dimension, embedding)
                VALUES
                    (:chunk_id, :model_name, :dimension, CAST(:embedding AS vector))
            """),
            {
                "chunk_id": chunk_id,
                "model_name": embedding_service.model_name,
                "dimension": len(embedding),
                "embedding": str(embedding)
            }
        )

        print("\nDatabase seeding successful!")
        print("Document ID:", document_id)
        print("Chunk ID:", chunk_id)
        print("Embedding dimension:", len(embedding))

finally:
    engine.dispose()