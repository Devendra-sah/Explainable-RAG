from app.services.document_extractor import DocumentExtractor
from app.services.chunking_service import ChunkingService


file_path = "sample_test.docx"


extractor = DocumentExtractor()

chunker = ChunkingService(
    target_tokens=450,
    overlap_tokens=60,
    max_tokens=500
)


# ==================================================
# Extract DOCX
# ==================================================

document = extractor.extract(file_path)

print("\nDOCX EXTRACTION")
print("=" * 70)

print(
    "File type:",
    document["file_type"]
)

print(
    "Total blocks:",
    len(document["blocks"])
)


# ==================================================
# Group paragraphs by section
# ==================================================

sections = []

current_section = None
current_paragraphs = []


for block in document["blocks"]:

    if block["type"] == "heading":

        # Save previous section
        if current_paragraphs:

            sections.append({
                "title": current_section,
                "text": "\n\n".join(
                    current_paragraphs
                )
            })

        current_section = block["text"]

        current_paragraphs = []

    else:

        current_paragraphs.append(
            block["text"]
        )


# Save final section

if current_paragraphs:

    sections.append({
        "title": current_section,
        "text": "\n\n".join(
            current_paragraphs
        )
    })


# ==================================================
# Chunk sections
# ==================================================

chunks = []

global_chunk_index = 0


for section in sections:

    section_chunks = chunker.chunk_text(
        section["text"],
        section_title=section["title"]
    )

    for chunk in section_chunks:

        global_chunk_index += 1

        chunk["chunk_index"] = (
            global_chunk_index
        )

        chunks.append(chunk)


# ==================================================
# Display
# ==================================================

print("\nSECTIONS FOUND:", len(sections))

for section in sections:

    print(
        f"- {section['title']}"
    )


print("\nTOTAL CHUNKS:", len(chunks))

print("\nCHUNK DETAILS")
print("=" * 70)


for chunk in chunks:

    print(
        f"\nChunk {chunk['chunk_index']}"
    )

    print(
        "Section:",
        chunk["section_title"]
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