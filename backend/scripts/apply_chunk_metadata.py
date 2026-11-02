import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SQL_FILE = PROJECT_ROOT / "database" / "03_chunk_metadata.sql"

if not SQL_FILE.exists():
    raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")


sql = SQL_FILE.read_text(encoding="utf-8")

engine = create_engine(DATABASE_URL)


try:

    print("Connecting to Neon PostgreSQL...")

    with engine.begin() as connection:
        connection.execute(text(sql))

    print("Chunk metadata migration completed successfully.")

finally:

    engine.dispose()
    print("Database connection closed.")