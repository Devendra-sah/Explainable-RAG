import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


query_vector = [0.0] * 384


vector_string = (
    "[" +
    ",".join(
        str(value)
        for value in query_vector
    ) +
    "]"
)


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            EXPLAIN
            SELECT
                e.embedding_id,
                e.chunk_id,
                e.embedding <=> %s::vector
                    AS distance
            FROM embeddings e
            ORDER BY
                e.embedding <=> %s::vector
            LIMIT 5
            """,
            (
                vector_string,
                vector_string
            )
        )

        print("\nVECTOR QUERY PLAN")
        print("=" * 80)

        for row in cursor.fetchall():

            print(row[0])