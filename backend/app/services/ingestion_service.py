from pathlib import Path
import hashlib
import time

import psycopg
from psycopg.rows import dict_row

from app.services.document_extractor import DocumentExtractor
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


class DocumentIngestionService:

    def __init__(self, database_url: str):

        self.database_url = database_url

        self.extractor = DocumentExtractor()

        self.chunker = ChunkingService(
            target_tokens=450,
            overlap_tokens=60,
            max_tokens=500
        )

        self.embedding_service = EmbeddingService()


    # ==================================================
    # PUBLIC METHOD
    # ==================================================

    def ingest_document(self, file_path: str, user_id: int | None = None):

        start_time = time.perf_counter()

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        print("\n" + "=" * 70)
        print("DOCUMENT INGESTION")
        print("=" * 70)

        print("File:", path.name)

        # ------------------------------------------------
        # 1. Calculate file metadata
        # ------------------------------------------------

        file_hash = self._calculate_file_hash(path)

        file_size = path.stat().st_size

        file_type = path.suffix.lower().replace(".", "")

        print("File type:", file_type)
        print("File size:", file_size, "bytes")
        print("File hash:", file_hash)

        # ------------------------------------------------
        # Check for existing document
        # ------------------------------------------------

        existing_document = self._find_existing_document(file_hash, user_id)

        if existing_document:

            print("\nDocument already exists.")
            print(
                "Existing Document ID:",
                existing_document["document_id"]
            )

            return {
                "document_id": existing_document["document_id"],
                "file_name": existing_document["file_name"],
                "file_type": existing_document["file_type"],
                "file_hash": existing_document["file_hash"],
                "chunk_count": existing_document["chunk_count"],
                "already_exists": True
            }

        # ------------------------------------------------
        # 2. Extract document
        # ------------------------------------------------

        print("\nExtracting document...")

        extracted = self.extractor.extract(
            str(path)
        )

        print("Extraction successful.")

        # ------------------------------------------------
        # 3. Generate chunks
        # ------------------------------------------------

        print("\nGenerating chunks...")

        chunks = self._create_chunks(
            extracted
        )

        print(
            f"Generated {len(chunks)} chunks."
        )

        if not chunks:
            raise ValueError(
                "No text chunks were generated."
            )

        # ------------------------------------------------
        # 4. Database transaction
        # ------------------------------------------------

        print("\nStarting database transaction...")

        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as connection:

            try:

                with connection.cursor() as cursor:

                    # ====================================
                    # DOCUMENT
                    # ====================================

                    document_id = self._insert_document(
                        cursor=cursor,
                        title=path.stem,
                        file_name=path.name,
                        file_type=file_type,
                        file_hash=file_hash,
                        file_size=file_size,
                        user_id=user_id
                    )

                    print(
                        "Document ID:",
                        document_id
                    )

                    # ====================================
                    # CHUNKS + EMBEDDINGS
                    # ====================================

                    for chunk in chunks:

                        chunk_id = self._insert_chunk(
                            cursor=cursor,
                            document_id=document_id,
                            chunk=chunk
                        )

                        print(
                            f"  Chunk {chunk['chunk_index']} "
                            f"→ DB ID {chunk_id} "
                            f"→ {chunk['token_count']} tokens"
                        )

                        # -------------------------------
                        # Generate embedding
                        # -------------------------------

                        embedding = (
                            self.embedding_service
                            .generate_embedding(
                                chunk["text"]
                            )
                        )

                        self._insert_embedding(
                            cursor=cursor,
                            chunk_id=chunk_id,
                            embedding=embedding
                        )

                # ====================================
                # COMMIT
                # ====================================

                connection.commit()

                print("\nTransaction committed successfully.")

            except Exception:

                connection.rollback()

                print(
                    "\nTransaction failed."
                )

                print(
                    "All database changes were rolled back."
                )

                raise

        elapsed = (
            time.perf_counter() - start_time
        )

        print(
            f"\nIngestion completed in "
            f"{elapsed:.2f} seconds."
        )

        return {
            "document_id": document_id,
            "file_name": path.name,
            "file_type": file_type,
            "file_hash": file_hash,
            "chunk_count": len(chunks),
            "elapsed_seconds": elapsed
        }


    # ==================================================
    # CREATE CHUNKS
    # ==================================================

    def _create_chunks(self, extracted):

        file_type = extracted["file_type"]

        chunks = []

        global_chunk_index = 0


        # ==================================================
        # PDF
        # ==================================================

        if file_type == "pdf":

            for page in extracted["pages"]:

                page_chunks = (
                    self.chunker.chunk_text(
                        page["text"],
                        page_number=page["page_number"]
                    )
                )

                for chunk in page_chunks:

                    global_chunk_index += 1

                    chunk["chunk_index"] = (
                        global_chunk_index
                    )

                    chunks.append(chunk)


        # ==================================================
        # TXT
        # ==================================================

        elif file_type == "txt":

            text_chunks = (
                self.chunker.chunk_text(
                    extracted["text"]
                )
            )

            for chunk in text_chunks:

                global_chunk_index += 1

                chunk["chunk_index"] = (
                    global_chunk_index
                )

                chunks.append(chunk)


        # ==================================================
        # DOCX
        # ==================================================

        elif file_type == "docx":

            sections = []

            current_section = None
            current_paragraphs = []


            for block in extracted["blocks"]:

                if block["type"] == "heading":

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


            # Chunk sections

            for section in sections:

                section_chunks = (
                    self.chunker.chunk_text(
                        section["text"],
                        section_title=section["title"]
                    )
                )

                for chunk in section_chunks:

                    global_chunk_index += 1

                    chunk["chunk_index"] = (
                        global_chunk_index
                    )

                    chunks.append(chunk)


        else:

            raise ValueError(
                f"Unsupported file type: {file_type}"
            )


        return chunks


    # ==================================================
    # INSERT DOCUMENT
    # ==================================================

    def _insert_document(
        self,
        cursor,
        title,
        file_name,
        file_type,
        file_hash,
        file_size,
        user_id
    ):

        query = """
            INSERT INTO documents (
                title,
                file_name,
                file_type,
                file_hash,
                file_size_bytes,
                user_id
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING document_id
        """

        cursor.execute(
            query,
            (
                title,
                file_name,
                file_type,
                file_hash,
                file_size,
                user_id
            )
        )

        return cursor.fetchone()["document_id"]


    # ==================================================
    # INSERT CHUNK
    # ==================================================

    def _insert_chunk(
        self,
        cursor,
        document_id,
        chunk
    ):

        query = """
            INSERT INTO chunks (
                document_id,
                chunk_text,
                chunk_index,
                page_number,
                section_title,
                token_count
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING chunk_id
        """

        cursor.execute(
            query,
            (
                document_id,
                chunk["text"],
                chunk["chunk_index"],
                chunk.get("page_number"),
                chunk.get("section_title"),
                chunk["token_count"]
            )
        )

        return cursor.fetchone()["chunk_id"]


    # ==================================================
    # INSERT EMBEDDING
    # ==================================================

    def _insert_embedding(
        self,
        cursor,
        chunk_id,
        embedding
    ):

        dimension = len(embedding)

        vector_string = (
            "[" +
            ",".join(
                str(value)
                for value in embedding
            ) +
            "]"
        )

        query = """
            INSERT INTO embeddings (
                chunk_id,
                model_name,
                dimension,
                embedding
            )
            VALUES (
                %s,
                %s,
                %s,
                %s::vector
            )
        """

        cursor.execute(
            query,
            (
                chunk_id,
                self.embedding_service.model_name,
                dimension,
                vector_string
            )
        )


    # ==================================================
    # FILE HASH
    # ==================================================

    def _calculate_file_hash(
        self,
        path: Path
    ):

        sha256 = hashlib.sha256()

        with path.open("rb") as file:

            while True:

                data = file.read(1024 * 1024)

                if not data:
                    break

                sha256.update(data)

        return sha256.hexdigest()

    def _find_existing_document(self, file_hash, user_id):

        query = """
            SELECT
                d.document_id,
                d.file_name,
                d.file_type,
                d.file_hash,
                COUNT(c.chunk_id) AS chunk_count
            FROM documents d
            LEFT JOIN chunks c
                ON d.document_id = c.document_id
            WHERE d.file_hash = %s AND d.user_id = %s
            GROUP BY
                d.document_id,
                d.file_name,
                d.file_type,
                d.file_hash
        """

        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    query,
                    (file_hash, user_id)
                )

                return cursor.fetchone()