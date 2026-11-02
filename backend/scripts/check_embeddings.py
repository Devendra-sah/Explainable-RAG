from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    e.embedding_id,
                    e.chunk_id,
                    e.model_name,
                    e.dimension,
                    e.embedding
                FROM embeddings e
                ORDER BY e.embedding_id;
            """)
        )

        rows = result.fetchall()

        print("\nEmbeddings in database:")
        print("-" * 70)

        for row in rows:
            print("Embedding ID :", row.embedding_id)
            print("Chunk ID     :", row.chunk_id)
            print("Model        :", row.model_name)
            print("Dimension    :", row.dimension)
            print("Vector type  :", type(row.embedding).__name__)
            print("Vector start :", str(row.embedding)[:100])
            print()

        print("Total embeddings:", len(rows))

finally:
    engine.dispose()