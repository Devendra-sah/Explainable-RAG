import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


query = text("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")


with engine.connect() as connection:

    result = connection.execute(query)

    print("\nTables in database:")
    print("------------------")

    for row in result:
        print(row[0])


engine.dispose()