class ContextBuilder:
    """Build model context and trusted source metadata."""

    def build(self, retrieval_results):
        sources = []
        context_parts = []

        for result in retrieval_results:
            label = f"S{len(sources) + 1}"

            source = {
                "citation_label": label,
                "chunk_id": result["chunk_id"],
                "document_id": result["document_id"],
                "title": result["title"],
                "file_name": result["file_name"],
                "file_type": result["file_type"],
                "chunk_index": result["chunk_index"],
                "page_number": result["page_number"],
                "section_title": result["section_title"],
                "rank": result["rank"],
                "similarity_score": float(result["similarity_score"]),
                "chunk_text": result["chunk_text"],
            }

            sources.append(source)

            metadata = [
                f"Citation: [{label}]",
                f"Title: {source['title']}",
                f"File: {source['file_name']}",
                f"Chunk ID: {source['chunk_id']}",
                f"Chunk index: {source['chunk_index']}",
            ]

            if source["page_number"] is not None:
                metadata.append(f"Page: {source['page_number']}")

            if source["section_title"]:
                metadata.append(f"Section: {source['section_title']}")

            context_parts.append(
                "\n".join(metadata) + "\nText:\n" + source["chunk_text"]
            )

        context = "\n\n--- SOURCE SEPARATOR ---\n\n".join(context_parts)

        return {
            "context": context,
            "sources": sources,
        }
