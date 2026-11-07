import time
import psycopg
from psycopg.rows import dict_row
from app.services.embedding_service import EmbeddingService


class RetrievalService:

    def __init__(self, database_url: str):

        self.database_url = database_url

        self.embedding_service = EmbeddingService()

    # ==================================================
    # SEARCH
    # ==================================================

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ):

        if not query_text.strip():
            raise ValueError("Query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        total_start = time.perf_counter()

        # ==============================================
        # 1. Generate query embedding
        # ==============================================

        embedding_start = time.perf_counter()

        query_embedding = self.embedding_service.generate_embedding(query_text)

        embedding_time_ms = (time.perf_counter() - embedding_start) * 1000

        vector_string = "[" + ",".join(str(value) for value in query_embedding) + "]"

        # ==============================================
        # 2. Database transaction
        # ==============================================

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:

            with connection.cursor() as cursor:

                # ======================================
                # Store query
                # ======================================

                ownership_filters = []
                retrieval_params = [vector_string]
                if user_id is not None:
                    ownership_filters.append("d.user_id = %s")
                    retrieval_params.append(user_id)
                if conversation_id is not None:
                    ownership_filters.append(
                        "EXISTS (SELECT 1 FROM conversation_documents cd "
                        "WHERE cd.document_id = d.document_id "
                        "AND cd.conversation_id = %s)"
                    )
                    retrieval_params.append(conversation_id)
                ownership_clause = (
                    "WHERE " + " AND ".join(ownership_filters)
                    if ownership_filters else ""
                )
                retrieval_params.extend([vector_string, top_k])
                cursor.execute(
                    f"""
                    INSERT INTO queries (
                        query_text,
                        top_k,
                        user_id,
                        conversation_id
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING query_id
                    """,
                    (query_text, top_k, user_id, conversation_id),
                )

                query_id = cursor.fetchone()["query_id"]

                # ======================================
                # 3. Vector retrieval
                # ======================================

                retrieval_start = time.perf_counter()

                cursor.execute(
                    f"""
                    SELECT
                        c.chunk_id,
                        c.chunk_text,
                        c.chunk_index,
                        c.page_number,
                        c.section_title,

                        d.document_id,
                        d.title,
                        d.file_name,
                        d.file_type,

                        1 - (
                            e.embedding
                            <=>
                            %s::vector
                        ) AS similarity_score

                    FROM embeddings e

                    JOIN chunks c
                        ON e.chunk_id = c.chunk_id

                    JOIN documents d
                        ON c.document_id =
                           d.document_id

                    {ownership_clause}

                    ORDER BY
                        e.embedding
                        <=>
                        %s::vector

                    LIMIT %s
                    """,
                    retrieval_params,
                )

                results = cursor.fetchall()

                retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

                # ======================================
                # 4. Store retrieval results
                # ======================================

                for rank, result in enumerate(results, start=1):

                    cursor.execute(
                        """
                        INSERT INTO retrieval_results (
                            query_id,
                            chunk_id,
                            rank,
                            similarity_score
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            query_id,
                            result["chunk_id"],
                            rank,
                            float(result["similarity_score"]),
                        ),
                    )

                    result["rank"] = rank

                # ======================================
                # 5. Retrieval log
                # ======================================

                total_latency_ms = (time.perf_counter() - total_start) * 1000

                cursor.execute(
                    """
                    INSERT INTO retrieval_logs (
                        query_id,
                        embedding_time_ms,
                        retrieval_time_ms,
                        total_latency_ms,
                        candidate_count,
                        result_count
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        (
                            query_id,
                            embedding_time_ms,
                            retrieval_time_ms,
                            total_latency_ms,
                            len(results),
                            len(results),
                        )
                    ),
                )

            connection.commit()

        return {
            "query_id": query_id,
            "query_text": query_text,
            "top_k": top_k,
            "results": results,
            "embedding_time_ms": embedding_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "total_latency_ms": total_latency_ms,
        }
