import os
import json
from pathlib import Path

from dotenv import load_dotenv
from app.services.rag_service import RAGService

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from backend/.env")

rag_service = RAGService(database_url=database_url)

question = input("Enter your question: ").strip()

result = rag_service.generate_answer(
    question=question,
    top_k=5,
)

print("\n" + "=" * 60)
print("GENERATED ANSWER")
print("=" * 60)
print(result["answer"])

print("\n" + "=" * 60)
print("SOURCES")
print("=" * 60)

for source in result["sources"]:
    print(
        f"[{source['citation_label']}] "
        f"{source['title']} | "
        f"Chunk ID: {source['chunk_id']} | "
        f"Similarity: {source['similarity_score']:.4f}"
    )

    if source["page_number"] is not None:
        print(f"    Page: {source['page_number']}")

    if source["section_title"]:
        print(f"    Section: {source['section_title']}")

print("\n" + "=" * 60)
print("METRICS")
print("=" * 60)
print("Answer ID:", result["answer_id"])
print("Query ID:", result["query_id"])
print("Model:", result["model"])
print("Generation latency:", result["generation_latency_ms"], "ms")
print("Retrieval metrics:", result["retrieval"])

print("\nComplete result:")
print(json.dumps(result, indent=2, default=str))
