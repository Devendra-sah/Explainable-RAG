import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


query = text("""
    SELECT
        tablename,
        indexname
    FROM pg_indexes
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname;
""")


with engine.connect() as connection:

    result = connection.execute(query)

    print("\nIndexes in database:")
    print("-------------------")

    for row in result:
        print(f"{row[0]} -> {row[1]}")


engine.dispose()