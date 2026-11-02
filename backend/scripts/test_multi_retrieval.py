import os

from dotenv import load_dotenv

from app.services.retrieval_service import (
    RetrievalService
)


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


service = RetrievalService(
    DATABASE_URL
)


queries = [
    "What is database normalization?",
    "What is First Normal Form?",
    "How does database indexing improve retrieval?"
]


for query in queries:

    print("\n")
    print("=" * 80)
    print("QUERY:", query)
    print("=" * 80)


    result = service.search(
        query_text=query,
        top_k=5
    )


    print(
        "\nQuery ID:",
        result["query_id"]
    )

    print(
        "Embedding time:",
        f"{result['embedding_time_ms']:.2f} ms"
    )

    print(
        "Retrieval time:",
        f"{result['retrieval_time_ms']:.2f} ms"
    )

    print(
        "Total latency:",
        f"{result['total_latency_ms']:.2f} ms"
    )


    print("\nRESULTS")
    print("-" * 80)


    for item in result["results"]:

        print(
            f"\nRank: {item['rank']}"
        )

        print(
            "Document:",
            item["title"]
        )

        print(
            "File:",
            item["file_name"]
        )

        print(
            "Chunk:",
            item["chunk_id"]
        )

        print(
            "Section:",
            item["section_title"]
        )

        print(
            "Page:",
            item["page_number"]
        )

        print(
            "Similarity:",
            f"{float(item['similarity_score']):.4f}"
        )

        print(
            "Text:",
            item["chunk_text"][:250],
            "..."
        )