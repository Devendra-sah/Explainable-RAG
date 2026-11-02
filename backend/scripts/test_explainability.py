import os

from dotenv import load_dotenv

from app.services.explainability_service import (
    ExplainabilityService
)


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


QUERY_ID = 2


service = ExplainabilityService(
    DATABASE_URL
)


results = service.explain_query(
    QUERY_ID
)


print("\n")
print("=" * 80)
print("EXPLAINABILITY RESULTS")
print("=" * 80)


for result in results:

    print("\n")
    print(
        f"Rank #{result['rank']}"
    )

    print(
        "Document:",
        result["title"]
    )

    print(
        "Section:",
        result["section_title"]
    )

    print(
        "Similarity:",
        f"{float(result['similarity_score']):.4f}"
    )

    print(
        "Semantic score:",
        f"{float(result['semantic_score']):.4f}"
    )

    print(
        "Keyword score:",
        f"{float(result['keyword_score']):.4f}"
    )

    print(
        "Metadata score:",
        f"{float(result['metadata_score']):.4f}"
    )

    print(
        "Ranking score:",
        f"{float(result['ranking_score']):.4f}"
    )

    print(
        "Explainability score:",
        f"{float(result['explainability_score']):.4f}"
    )

    print(
        "\nWHY RETRIEVED?"
    )

    print(
        result["explanation_text"]
    )

    print("-" * 80)