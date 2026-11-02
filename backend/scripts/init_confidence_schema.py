import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# ==========================================================
# Load environment variables
# ==========================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not found in backend/.env"
    )


# ==========================================================
# Execute SQL file
# ==========================================================

def execute_sql_file(sql_file):

    sql_path = PROJECT_ROOT / "database" / sql_file

    print()
    print(f"Applying: {sql_path}")

    if not sql_path.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_path}"
        )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    with psycopg.connect(DATABASE_URL) as conn:

        with conn.cursor() as cur:
            cur.execute(sql)

        conn.commit()

    print(
        f"Successfully applied: {sql_file}"
    )


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    execute_sql_file(
        "05_confidence_schema.sql"
    )

    execute_sql_file(
        "06_query_explanations.sql"
    )

    print()
    print("=" * 70)
    print("F3 CONFIDENCE SCHEMA INITIALIZED")
    print("=" * 70)