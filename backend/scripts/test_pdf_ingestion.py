from app.services.document_extractor import DocumentExtractor
from app.services.chunking_service import ChunkingService


file_path = "sample_test.pdf"


extractor = DocumentExtractor()

chunker = ChunkingService(
    target_tokens=450,
    overlap_tokens=60,
    max_tokens=500
)


# ==================================================
# Extract PDF
# ==================================================

document = extractor.extract(file_path)

print("\nPDF EXTRACTION")
print("=" * 70)

print("File type:", document["file_type"])
print("Page count:", document["page_count"])


# ==================================================
# Chunk pages
# ==================================================

chunks = []

global_chunk_index = 0

for page in document["pages"]:

    page_chunks = chunker.chunk_text(
        page["text"],
        page_number=page["page_number"]
    )

    for chunk in page_chunks:

        global_chunk_index += 1

        chunk["chunk_index"] = (
            global_chunk_index
        )

        chunks.append(chunk)


# ==================================================
# Display
# ==================================================

print("\nTOTAL CHUNKS:", len(chunks))

print("\nCHUNK DETAILS")
print("=" * 70)

for chunk in chunks:

    print(
        f"\nChunk {chunk['chunk_index']}"
    )

    print(
        "Page:",
        chunk["page_number"]
    )

    print(
        "Tokens:",
        chunk["token_count"]
    )

    print(
        "Text:",
        chunk["text"][:300],
        "..."
    )

    print("-" * 70)