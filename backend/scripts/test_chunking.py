from app.services.document_extractor import DocumentExtractor
from app.services.chunking_service import ChunkingService


file_path = "sample.txt"


# --------------------------------------------------
# Initialize services
# --------------------------------------------------

extractor = DocumentExtractor()

chunker = ChunkingService(
    target_tokens=450,
    overlap_tokens=60,
    max_tokens=500
)


# --------------------------------------------------
# Extract document
# --------------------------------------------------

document = extractor.extract(
    file_path
)


print("\nDocument extraction successful.")
print("File type:", document["file_type"])


# --------------------------------------------------
# TXT
# --------------------------------------------------

if document["file_type"] == "txt":

    chunks = chunker.chunk_text(
        document["text"]
    )


# --------------------------------------------------
# PDF
# --------------------------------------------------

elif document["file_type"] == "pdf":

    chunks = []

    for page in document["pages"]:

        page_chunks = chunker.chunk_text(
            page["text"],
            page_number=page["page_number"]
        )

        chunks.extend(
            page_chunks
        )


# --------------------------------------------------
# DOCX
# --------------------------------------------------

elif document["file_type"] == "docx":

    chunks = []

    current_section = None

    for paragraph in document["paragraphs"]:

        style = paragraph["style"]

        if style.startswith("Heading"):

            current_section = paragraph["text"]

            continue


        paragraph_chunks = chunker.chunk_text(
            paragraph["text"],
            section_title=current_section
        )

        chunks.extend(
            paragraph_chunks
        )


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\nTotal chunks:", len(chunks))

print("\nChunk Details")
print("=" * 70)


for index, chunk in enumerate(
    chunks,
    start=1
):

    print(f"\nChunk {index}")

    print(
        "Page:",
        chunk["page_number"]
    )

    print(
        "Section:",
        chunk["section_title"]
    )

    print(
        "Token count:",
        chunk["token_count"]
    )

    print("\nText:")
    print(chunk["text"])

    print("-" * 70)

# --------------------------------------------------
# Verify overlap
# --------------------------------------------------

print("\n\nOverlap Verification")
print("=" * 70)

for i in range(len(chunks) - 1):

    current_tokens = chunker.tokenizer.encode(
        chunks[i]["text"],
        add_special_tokens=False
    )

    next_tokens = chunker.tokenizer.encode(
        chunks[i + 1]["text"],
        add_special_tokens=False
    )

    max_possible = min(
        len(current_tokens),
        len(next_tokens),
        100
    )

    overlap = 0

    for size in range(
        max_possible,
        0,
        -1
    ):

        if current_tokens[-size:] == next_tokens[:size]:
            overlap = size
            break

    print(
        f"Chunk {i + 1} → Chunk {i + 2}: "
        f"{overlap} overlapping tokens"
    )