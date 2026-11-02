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
        "DATABASE_URL is not set. "
        "Check your backend/.env file."
    )


# ------------------------------------------------------------
# Locate schema.sql
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_FILE = PROJECT_ROOT / "database" / "01_schema.sql"


if not SCHEMA_FILE.exists():
    raise FileNotFoundError(
        f"Schema file not found: {SCHEMA_FILE}"
    )


# ------------------------------------------------------------
# Read SQL schema
# ------------------------------------------------------------

schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")


# ------------------------------------------------------------
# Connect to Neon PostgreSQL
# ------------------------------------------------------------

print("Connecting to Neon PostgreSQL...")

engine = create_engine(DATABASE_URL)


# ------------------------------------------------------------
# Execute schema
# ------------------------------------------------------------

try:

    with engine.connect() as connection:

        print("Connected successfully.")

        # PostgreSQL accepts multiple SQL statements through
        # psycopg when executed as a text block.
        connection.execute(text(schema_sql))

        connection.commit()

        print("Database schema created successfully!")


except Exception as error:

    print("\nDatabase initialization failed.")
    print("Error:")
    print(error)

    raise


finally:

    engine.dispose()

    print("\nDatabase connection closed.")