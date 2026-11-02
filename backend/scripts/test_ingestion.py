import os

from dotenv import load_dotenv

from app.services.ingestion_service import (
    DocumentIngestionService
)


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


# Change this file when testing another format.
FILE_PATH = "sample_test.docx"


service = DocumentIngestionService(
    database_url=DATABASE_URL
)


result = service.ingest_document(
    FILE_PATH
)


print("\n" + "=" * 70)
print("INGESTION RESULT")
print("=" * 70)

for key, value in result.items():

    print(
        f"{key}: {value}"
    )