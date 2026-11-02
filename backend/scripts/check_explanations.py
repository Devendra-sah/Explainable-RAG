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

        print("\nEXPLANATIONS")
        print("=" * 80)

        cursor.execute("""
            SELECT
                explanation_id,
                result_id,
                semantic_score,
                keyword_score,
                metadata_score,
                ranking_score,
                explainability_score,
                explanation_text
            FROM explanations
            ORDER BY explanation_id DESC
        """)

        for row in cursor.fetchall():

            print(row)


        print("\nEVIDENCE")
        print("=" * 80)

        cursor.execute("""
            SELECT
                evidence_id,
                explanation_id,
                evidence_type,
                evidence_text,
                contribution_score,
                evidence_rank
            FROM explanation_evidence
            ORDER BY
                explanation_id DESC,
                evidence_rank
        """)

        for row in cursor.fetchall():

            print(row)