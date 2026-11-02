import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        # ==========================================
        # Queries
        # ==========================================

        print("\nQUERIES")
        print("=" * 80)

        cursor.execute("""
            SELECT
                query_id,
                query_text,
                top_k,
                created_at
            FROM queries
            ORDER BY query_id DESC
            LIMIT 10
        """)

        for row in cursor.fetchall():

            print(row)


        # ==========================================
        # Retrieval results
        # ==========================================

        print("\nRETRIEVAL RESULTS")
        print("=" * 80)

        cursor.execute("""
            SELECT
                rr.result_id,
                rr.query_id,
                rr.chunk_id,
                rr.rank,
                rr.similarity_score,
                d.title,
                c.section_title
            FROM retrieval_results rr

            JOIN chunks c
                ON rr.chunk_id = c.chunk_id

            JOIN documents d
                ON c.document_id = d.document_id

            ORDER BY rr.result_id DESC

            LIMIT 20
        """)

        for row in cursor.fetchall():

            print(row)


        # ==========================================
        # Retrieval logs
        # ==========================================

        print("\nRETRIEVAL LOGS")
        print("=" * 80)

        cursor.execute("""
            SELECT
                log_id,
                query_id,
                embedding_time_ms,
                retrieval_time_ms,
                total_latency_ms,
                candidate_count,
                result_count,
                created_at
            FROM retrieval_logs
            ORDER BY log_id DESC
            LIMIT 10
        """)

        for row in cursor.fetchall():

            print(row)