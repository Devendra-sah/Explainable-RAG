"""Apply the additive multi-user migration to an existing database."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set in backend/.env")

schema_file = Path(__file__).resolve().parents[2] / "database" / "07_multi_user.sql"
with psycopg.connect(database_url) as connection:
    connection.execute(schema_file.read_text(encoding="utf-8"))
    connection.commit()

print("Multi-user ownership and conversation migration applied.")
