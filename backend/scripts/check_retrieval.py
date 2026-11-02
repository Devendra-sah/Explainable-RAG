import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)


try:

    with engine.connect() as connection:

        print("\nQUERIES")
        print("=" * 70)

        queries = connection.execute(
            text("""
                SELECT
                    query_id,
                    query_text,
                    top_k,
                    created_at
                FROM queries
                ORDER BY query_id;
            """)
        )

        for row in queries:

            print(f"Query ID   : {row.query_id}")
            print(f"Query      : {row.query_text}")
            print(f"Top K      : {row.top_k}")
            print(f"Created At : {row.created_at}")
            print("-" * 70)


        print("\nRETRIEVAL RESULTS")
        print("=" * 70)

        results = connection.execute(
            text("""
                SELECT
                    rr.result_id,
                    rr.query_id,
                    rr.chunk_id,
                    rr.rank,
                    rr.similarity_score
                FROM retrieval_results rr
                ORDER BY rr.result_id;
            """)
        )

        for row in results:

            print(f"Result ID          : {row.result_id}")
            print(f"Query ID           : {row.query_id}")
            print(f"Chunk ID           : {row.chunk_id}")
            print(f"Rank               : {row.rank}")
            print(f"Similarity Score   : {row.similarity_score:.4f}")
            print("-" * 70)


finally:

    engine.dispose()