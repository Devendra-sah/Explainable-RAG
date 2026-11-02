import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Check backend/.env"
    )


# ------------------------------------------------------------
# Locate index file
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INDEX_FILE = PROJECT_ROOT / "database" / "02_indexes.sql"


if not INDEX_FILE.exists():
    raise FileNotFoundError(
        f"Index file not found: {INDEX_FILE}"
    )


# ------------------------------------------------------------
# Read SQL
# ------------------------------------------------------------

index_sql = INDEX_FILE.read_text(encoding="utf-8")


# ------------------------------------------------------------
# Connect to Neon
# ------------------------------------------------------------

print("Connecting to Neon PostgreSQL...")

engine = create_engine(DATABASE_URL)


try:

    with engine.connect() as connection:

        print("Connected successfully.")

        connection.execute(text(index_sql))

        connection.commit()

        print("Indexes created successfully!")


except Exception as error:

    print("\nIndex creation failed.")
    print("Error:")
    print(error)

    raise


finally:

    engine.dispose()

    print("\nDatabase connection closed.")