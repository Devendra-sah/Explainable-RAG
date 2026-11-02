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

        print("\nDOCUMENTS")
        print("=" * 70)

        cursor.execute("""
            SELECT
                document_id,
                title,
                file_name,
                file_type,
                file_hash,
                file_size_bytes
            FROM documents
            ORDER BY document_id DESC
        """)

        for row in cursor.fetchall():

            print(row)


        print("\nCHUNKS")
        print("=" * 70)

        cursor.execute("""
            SELECT
                c.chunk_id,
                c.document_id,
                c.chunk_index,
                c.page_number,
                c.section_title,
                c.token_count
            FROM chunks c
            ORDER BY c.chunk_id DESC
        """)

        for row in cursor.fetchall():

            print(row)


        print("\nEMBEDDINGS")
        print("=" * 70)

        cursor.execute("""
            SELECT
                embedding_id,
                chunk_id,
                model_name,
                dimension
            FROM embeddings
            ORDER BY embedding_id DESC
        """)

        for row in cursor.fetchall():

            print(row)