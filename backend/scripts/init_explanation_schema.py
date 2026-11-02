import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SQL_FILE = (
    PROJECT_ROOT
    / "database"
    / "04_explanation_evidence.sql"
)


sql = SQL_FILE.read_text(
    encoding="utf-8"
)


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        cursor.execute(sql)

    connection.commit()


print(
    "Explanation evidence schema created successfully."
)