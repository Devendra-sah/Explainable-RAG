import re

import psycopg
from psycopg.rows import dict_row


class ExplainabilityService:

    # ============================================================
    # STOP WORDS
    # ============================================================

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "with",
        "why",
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, database_url: str):
        self.database_url = database_url

    # ============================================================
    # MAIN EXPLANATION METHOD
    # ============================================================

    def explain_query(self, query_id: int):

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:

            try:

                with connection.cursor() as cursor:

                    # ==================================================
                    # 1. QUERY
                    # ==================================================

                    cursor.execute(
                        """
                        SELECT
                            query_id,
                            query_text,
                            top_k
                        FROM queries
                        WHERE query_id = %s
                        """,
                        (query_id,),
                    )

                    query = cursor.fetchone()

                    if not query:
                        raise ValueError(f"Query {query_id} not found.")

                    # ==================================================
                    # 2. RETRIEVAL RESULTS
                    # ==================================================

                    cursor.execute(
                        """
                        SELECT
                            rr.result_id,
                            rr.rank,
                            rr.similarity_score,

                            c.chunk_id,
                            c.chunk_text,
                            c.page_number,
                            c.section_title,

                            d.document_id,
                            d.title,
                            d.file_name,
                            d.file_type

                        FROM retrieval_results rr

                        JOIN chunks c
                            ON rr.chunk_id = c.chunk_id

                        JOIN documents d
                            ON c.document_id = d.document_id

                        WHERE rr.query_id = %s

                        ORDER BY rr.rank
                        """,
                        (query_id,),
                    )

                    results = cursor.fetchall()

                    if not results:
                        raise ValueError(
                            f"No retrieval results " f"found for query {query_id}."
                        )

                    # ==================================================
                    # 3. ANALYZE QUERY
                    # ==================================================

                    query_terms = self._extract_terms(query["query_text"])

                    # ==================================================
                    # F3 DATA COLLECTION
                    # ==================================================

                    confidence_scores = []
                    explainability_scores = []
                    similarity_scores = []

                    # ==================================================
                    # 4. GENERATE RESULT-LEVEL EXPLANATIONS
                    # ==================================================

                    for index, result in enumerate(results):

                        similarity_score = float(result["similarity_score"])

                        similarity_scores.append(similarity_score)

                        # ------------------------------------------------
                        # Semantic relevance
                        # ------------------------------------------------

                        semantic_score = self._semantic_score(similarity_score)

                        # ------------------------------------------------
                        # Keyword relevance
                        # ------------------------------------------------

                        keyword_score = self._keyword_score(
                            query_terms, result["chunk_text"]
                        )

                        # ------------------------------------------------
                        # Metadata relevance
                        # ------------------------------------------------

                        metadata_score = self._metadata_score(query_terms, result)

                        # ------------------------------------------------
                        # Score margin
                        # ------------------------------------------------

                        score_margin = self._score_margin(results, index)

                        # ------------------------------------------------
                        # Explainability score
                        #
                        # Rank is NOT included.
                        # ------------------------------------------------

                        explainability_score = self._calculate_explainability_score(
                            semantic_score, keyword_score, metadata_score, score_margin
                        )

                        # ==================================================
                        # F3 — CONFIDENCE SCORE
                        # ==================================================

                        confidence_score = self._calculate_confidence_score(
                            semantic_score, keyword_score, metadata_score, score_margin
                        )

                        confidence_level = self._get_confidence_level(confidence_score)

                        confidence_scores.append(confidence_score)

                        explainability_scores.append(explainability_score)

                        # ------------------------------------------------
                        # Comparative result
                        # ------------------------------------------------

                        comparison = self._compare_with_previous_result(results, index)

                        comparison_features = None

                        if comparison is not None:

                            competitor_index = comparison["competitor_index"]

                            competitor = results[competitor_index]

                            comparison_features = self._compare_features(
                                result, competitor, query_terms
                            )

                        # ------------------------------------------------
                        # Evidence
                        # ------------------------------------------------

                        evidence = self._build_evidence(
                            query_terms,
                            result,
                            semantic_score,
                            keyword_score,
                            metadata_score,
                            score_margin,
                            comparison,
                            comparison_features,
                            confidence_score,
                            confidence_level,
                        )

                        # ------------------------------------------------
                        # Natural language explanation
                        # ------------------------------------------------

                        explanation_text = self._generate_explanation_text(
                            result,
                            semantic_score,
                            keyword_score,
                            metadata_score,
                            score_margin,
                            explainability_score,
                            confidence_score,
                            confidence_level,
                            evidence,
                            comparison,
                            comparison_features,
                        )

                        # ==================================================
                        # 5. PERSIST RESULT-LEVEL EXPLANATION
                        # ==================================================

                        cursor.execute(
                            """
                            INSERT INTO explanations (
                                result_id,
                                semantic_score,
                                keyword_score,
                                metadata_score,
                                ranking_score,
                                explainability_score,
                                confidence_score,
                                confidence_level,
                                explanation_text
                            )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s
                            )

                            ON CONFLICT (result_id)
                            DO UPDATE SET

                                semantic_score =
                                    EXCLUDED.semantic_score,

                                keyword_score =
                                    EXCLUDED.keyword_score,

                                metadata_score =
                                    EXCLUDED.metadata_score,

                                ranking_score =
                                    EXCLUDED.ranking_score,

                                explainability_score =
                                    EXCLUDED.explainability_score,

                                confidence_score =
                                    EXCLUDED.confidence_score,

                                confidence_level =
                                    EXCLUDED.confidence_level,

                                explanation_text =
                                    EXCLUDED.explanation_text

                            RETURNING explanation_id
                            """,
                            (
                                result["result_id"],
                                semantic_score,
                                keyword_score,
                                metadata_score,
                                # Existing ranking score retained
                                # for compatibility.
                                self._rank_score(result["rank"], len(results)),
                                explainability_score,
                                confidence_score,
                                confidence_level,
                                explanation_text,
                            ),
                        )

                        explanation_id = cursor.fetchone()["explanation_id"]

                        # ==================================================
                        # 6. REPLACE EVIDENCE
                        # ==================================================

                        cursor.execute(
                            """
                            DELETE FROM explanation_evidence
                            WHERE explanation_id = %s
                            """,
                            (explanation_id,),
                        )

                        for evidence_rank, item in enumerate(evidence, start=1):

                            cursor.execute(
                                """
                                INSERT INTO explanation_evidence (
                                    explanation_id,
                                    evidence_type,
                                    evidence_text,
                                    contribution_score,
                                    evidence_rank
                                )
                                VALUES (
                                    %s,
                                    %s,
                                    %s,
                                    %s,
                                    %s
                                )
                                """,
                                (
                                    explanation_id,
                                    item["type"],
                                    item["text"],
                                    item["score"],
                                    evidence_rank,
                                ),
                            )

                    # ==================================================
                    # 7. F3 QUERY-LEVEL EXPLANATION
                    # ==================================================

                    query_explanation = self._build_query_level_explanation(
                        results,
                        confidence_scores,
                        explainability_scores,
                        similarity_scores,
                    )

                    # ==================================================
                    # 8. PERSIST QUERY-LEVEL EXPLANATION
                    # ==================================================

                    cursor.execute(
                        """
                        INSERT INTO query_explanations (
                            query_id,
                            overall_confidence_score,
                            confidence_level,
                            result_count,
                            top_similarity,
                            second_similarity,
                            similarity_margin,
                            average_similarity,
                            average_explainability,
                            explanation_text
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )

                        ON CONFLICT (query_id)
                        DO UPDATE SET

                            overall_confidence_score =
                                EXCLUDED.overall_confidence_score,

                            confidence_level =
                                EXCLUDED.confidence_level,

                            result_count =
                                EXCLUDED.result_count,

                            top_similarity =
                                EXCLUDED.top_similarity,

                            second_similarity =
                                EXCLUDED.second_similarity,

                            similarity_margin =
                                EXCLUDED.similarity_margin,

                            average_similarity =
                                EXCLUDED.average_similarity,

                            average_explainability =
                                EXCLUDED.average_explainability,

                            explanation_text =
                                EXCLUDED.explanation_text
                        """,
                        (
                            query_id,
                            query_explanation["overall_confidence_score"],
                            query_explanation["confidence_level"],
                            query_explanation["result_count"],
                            query_explanation["top_similarity"],
                            query_explanation["second_similarity"],
                            query_explanation["similarity_margin"],
                            query_explanation["average_similarity"],
                            query_explanation["average_explainability"],
                            query_explanation["explanation_text"],
                        ),
                    )

                    connection.commit()

            except Exception:

                connection.rollback()
                raise

        return self.get_query_explanations(query_id)

    # ============================================================
    # QUERY TERMS
    # ============================================================

    def _extract_terms(self, text: str):

        words = re.findall(r"[a-zA-Z0-9]+", text.lower())

        return {
            word for word in words if (len(word) > 2 and word not in self.STOP_WORDS)
        }

    # ============================================================
    # SEMANTIC SCORE
    # ============================================================

    def _semantic_score(self, similarity):

        # Convert cosine similarity [-1, 1]
        # into normalized score [0, 1].

        score = (similarity + 1) / 2

        return max(0.0, min(1.0, score))

    # ============================================================
    # KEYWORD SCORE
    # ============================================================

    def _keyword_score(self, query_terms, chunk_text):

        if not query_terms:
            return 0.0

        chunk_terms = self._extract_terms(chunk_text)

        overlap = query_terms.intersection(chunk_terms)

        return len(overlap) / len(query_terms)

    # ============================================================
    # METADATA SCORE
    # ============================================================

    def _metadata_score(self, query_terms, result):

        metadata_text = " ".join(
            [
                result.get("title") or "",
                result.get("file_name") or "",
                result.get("section_title") or "",
            ]
        )

        metadata_terms = self._extract_terms(metadata_text)

        if not query_terms:
            return 0.0

        overlap = query_terms.intersection(metadata_terms)

        return len(overlap) / len(query_terms)

    # ============================================================
    # RANK SCORE
    # ============================================================

    def _rank_score(self, rank, total_results):

        if total_results <= 1:
            return 1.0

        return (total_results - rank + 1) / total_results

    # ============================================================
    # SCORE MARGIN
    # ============================================================

    def _score_margin(self, results, index):

        current = float(results[index]["similarity_score"])

        # --------------------------------------------------------
        # Rank #1 compares against Rank #2.
        # --------------------------------------------------------

        if index == 0:

            if len(results) > 1:

                next_score = float(results[1]["similarity_score"])

                return max(0.0, current - next_score)

            return current

        # --------------------------------------------------------
        # Other ranks compare against previous rank.
        # --------------------------------------------------------

        previous = float(results[index - 1]["similarity_score"])

        return max(0.0, previous - current)

    # ============================================================
    # EXPLAINABILITY SCORE
    # ============================================================

    def _calculate_explainability_score(
        self, semantic_score, keyword_score, metadata_score, score_margin
    ):

        margin_score = min(score_margin * 5, 1.0)

        # IMPORTANT:
        # Rank is NOT included.
        #
        # 65% semantic
        # 20% keyword
        # 10% metadata
        # 5% margin

        score = (
            0.65 * semantic_score
            + 0.20 * keyword_score
            + 0.10 * metadata_score
            + 0.05 * margin_score
        )

        return max(0.0, min(1.0, score))

    # ============================================================
    # F3 — CONFIDENCE SCORE
    # ============================================================

    def _calculate_confidence_score(
        self, semantic_score, keyword_score, metadata_score, score_margin
    ):

        margin_score = min(score_margin * 5, 1.0)

        # --------------------------------------------------------
        # Confidence model
        #
        # 60% semantic relevance
        # 20% keyword agreement
        # 10% metadata agreement
        # 10% ranking separation
        #
        # This is intentionally different from
        # the explainability formula.
        # --------------------------------------------------------

        confidence = (
            0.60 * semantic_score
            + 0.20 * keyword_score
            + 0.10 * metadata_score
            + 0.10 * margin_score
        )

        return max(0.0, min(1.0, confidence))

    # ============================================================
    # F3 — CONFIDENCE LEVEL
    # ============================================================

    def _get_confidence_level(self, confidence_score):

        if confidence_score >= 0.80:
            return "HIGH"

        elif confidence_score >= 0.60:
            return "MEDIUM"

        return "LOW"

    # ============================================================
    # COMPARISON
    # ============================================================

    def _compare_with_previous_result(self, results, index):

        if len(results) < 2:
            return None

        # Rank #1 compares against Rank #2.

        if index == 0:

            return {
                "competitor_index": 1,
                "competitor_rank": 2,
                "competitor_score": float(results[1]["similarity_score"]),
                "score_difference": (
                    float(results[0]["similarity_score"])
                    - float(results[1]["similarity_score"])
                ),
            }

        # Every other result compares against
        # immediately preceding higher-ranked result.

        current = results[index]

        previous = results[index - 1]

        current_score = float(current["similarity_score"])

        previous_score = float(previous["similarity_score"])

        return {
            "competitor_index": index - 1,
            "competitor_rank": previous["rank"],
            "competitor_score": previous_score,
            "score_difference": (current_score - previous_score),
        }

    # ============================================================
    # COMPARE FEATURES
    # ============================================================

    def _compare_features(self, current, competitor, query_terms):

        current_keyword = self._keyword_score(query_terms, current["chunk_text"])

        competitor_keyword = self._keyword_score(query_terms, competitor["chunk_text"])

        current_metadata = self._metadata_score(query_terms, current)

        competitor_metadata = self._metadata_score(query_terms, competitor)

        current_similarity = float(current["similarity_score"])

        competitor_similarity = float(competitor["similarity_score"])

        return {
            "semantic_difference": (current_similarity - competitor_similarity),
            "keyword_difference": (current_keyword - competitor_keyword),
            "metadata_difference": (current_metadata - competitor_metadata),
        }

    # ============================================================
    # COMPARATIVE EXPLANATION
    # ============================================================

    def _generate_comparative_explanation(self, current, competitor, features):

        current_rank = current["rank"]

        competitor_rank = competitor["rank"]

        current_similarity = float(current["similarity_score"])

        competitor_similarity = float(competitor["similarity_score"])

        semantic_difference = features["semantic_difference"]

        keyword_difference = features["keyword_difference"]

        metadata_difference = features["metadata_difference"]

        # --------------------------------------------------------
        # Ranking direction
        # --------------------------------------------------------

        if current_rank < competitor_rank:

            explanation = (
                f"Rank #{current_rank} was placed above " f"Rank #{competitor_rank}. "
            )

        else:

            explanation = (
                f"Rank #{current_rank} was placed below " f"Rank #{competitor_rank}. "
            )

        # --------------------------------------------------------
        # Semantic similarity
        # --------------------------------------------------------

        if semantic_difference > 0.001:

            explanation += (
                f"Its cosine similarity was higher "
                f"({current_similarity:.4f} vs "
                f"{competitor_similarity:.4f}), "
                f"a difference of "
                f"{semantic_difference:.4f}. "
            )

        elif semantic_difference < -0.001:

            explanation += (
                f"Its cosine similarity was lower "
                f"({current_similarity:.4f} vs "
                f"{competitor_similarity:.4f}), "
                f"a difference of "
                f"{abs(semantic_difference):.4f}. "
            )

        else:

            explanation += "Both results had nearly identical " "cosine similarity. "

        # --------------------------------------------------------
        # Keyword comparison
        # --------------------------------------------------------

        if keyword_difference > 0.001:

            explanation += (
                f"Its keyword overlap was higher " f"by {keyword_difference:.2f}. "
            )

        elif keyword_difference < -0.001:

            explanation += (
                f"Its keyword overlap was lower " f"by {abs(keyword_difference):.2f}. "
            )

        else:

            explanation += "Keyword overlap was effectively equal. "

        # --------------------------------------------------------
        # Metadata comparison
        # --------------------------------------------------------

        if metadata_difference > 0.001:

            explanation += (
                "Its document or section metadata " "was more relevant to the query. "
            )

        elif metadata_difference < -0.001:

            explanation += (
                "Its document or section metadata " "was less relevant to the query. "
            )

        else:

            explanation += "Metadata relevance was effectively equal. "

        return explanation

    # ============================================================
    # EVIDENCE
    # ============================================================

    def _build_evidence(
        self,
        query_terms,
        result,
        semantic_score,
        keyword_score,
        metadata_score,
        score_margin,
        comparison,
        comparison_features,
        confidence_score,
        confidence_level,
    ):

        evidence = []

        # ========================================================
        # 1. TEXTUAL EVIDENCE
        # ========================================================

        snippet = self._extract_evidence_snippet(query_terms, result["chunk_text"])

        evidence.append(
            {
                "type": "textual_evidence",
                "text": ("Evidence from the retrieved chunk: " f'"{snippet}"'),
                "score": keyword_score,
            }
        )

        # ========================================================
        # 2. SEMANTIC EVIDENCE
        # ========================================================

        evidence.append(
            {
                "type": "semantic_similarity",
                "text": (
                    "The chunk has a cosine similarity "
                    f"of {float(result['similarity_score']):.4f} "
                    "with the query."
                ),
                "score": semantic_score,
            }
        )

        # ========================================================
        # 3. KEYWORD EVIDENCE
        # ========================================================

        chunk_terms = self._extract_terms(result["chunk_text"])

        matched_terms = sorted(query_terms.intersection(chunk_terms))

        if matched_terms:

            evidence.append(
                {
                    "type": "keyword_overlap",
                    "text": (
                        "The retrieved chunk contains "
                        "query-related terms: " + ", ".join(matched_terms) + "."
                    ),
                    "score": keyword_score,
                }
            )

        # ========================================================
        # 4. METADATA EVIDENCE
        # ========================================================

        metadata_values = []

        if result.get("title"):
            metadata_values.append(result["title"])

        if result.get("section_title"):
            metadata_values.append(result["section_title"])

        if metadata_values:

            evidence.append(
                {
                    "type": "metadata_relevance",
                    "text": ("Relevant metadata: " + " | ".join(metadata_values) + "."),
                    "score": metadata_score,
                }
            )

        # ========================================================
        # 5. SCORE MARGIN
        # ========================================================

        margin_score = min(score_margin * 5, 1.0)

        evidence.append(
            {
                "type": "score_margin",
                "text": (
                    "The similarity score margin "
                    "relative to the neighboring "
                    f"rank is {score_margin:.4f}."
                ),
                "score": margin_score,
            }
        )

        # ========================================================
        # 6. COMPARATIVE EVIDENCE
        # ========================================================

        if comparison is not None and comparison_features is not None:

            competitor_rank = comparison["competitor_rank"]

            comparison_text = self._generate_comparative_explanation(
                result,
                {
                    "rank": competitor_rank,
                    "similarity_score": comparison["competitor_score"],
                },
                comparison_features,
            )

            evidence.append(
                {
                    "type": "comparative_ranking",
                    "text": comparison_text,
                    "score": min(
                        abs(comparison_features["semantic_difference"]) * 5, 1.0
                    ),
                }
            )

        # ========================================================
        # 7. F3 CONFIDENCE EVIDENCE
        # ========================================================

        evidence.append(
            {
                "type": "confidence_assessment",
                "text": (
                    f"The retrieval confidence is "
                    f"{confidence_score:.3f}, classified as "
                    f"{confidence_level}."
                ),
                "score": confidence_score,
            }
        )

        return evidence

    # ============================================================
    # NATURAL LANGUAGE EXPLANATION
    # ============================================================

    def _generate_explanation_text(
        self,
        result,
        semantic_score,
        keyword_score,
        metadata_score,
        score_margin,
        explainability_score,
        confidence_score,
        confidence_level,
        evidence,
        comparison,
        comparison_features,
    ):

        # ========================================================
        # BASE EXPLANATION
        # ========================================================

        explanation = (
            f"This chunk was retrieved at rank "
            f"#{result['rank']} with a cosine "
            f"similarity of "
            f"{float(result['similarity_score']):.4f}. "
        )

        # ========================================================
        # KEYWORD RELEVANCE
        # ========================================================

        if keyword_score > 0:

            explanation += (
                f"It contains "
                f"{keyword_score * 100:.1f}% "
                "of the query's relevant terms. "
            )

        else:

            explanation += "It has no direct keyword overlap " "with the query. "

        # ========================================================
        # METADATA RELEVANCE
        # ========================================================

        if metadata_score > 0:

            explanation += (
                "Its document or section metadata " "is also relevant to the query. "
            )

        # ========================================================
        # TEXTUAL EVIDENCE
        # ========================================================

        for item in evidence:

            if item["type"] == "textual_evidence":

                explanation += item["text"] + " "

                break

        # ========================================================
        # SCORE MARGIN
        # ========================================================

        if score_margin > 0:

            explanation += (
                f"The similarity margin relative "
                "to the neighboring result is "
                f"{score_margin:.4f}. "
            )

        # ========================================================
        # COMPARATIVE EXPLANATION
        # ========================================================

        if comparison is not None and comparison_features is not None:

            competitor_rank = comparison["competitor_rank"]

            semantic_difference = comparison_features["semantic_difference"]

            keyword_difference = comparison_features["keyword_difference"]

            metadata_difference = comparison_features["metadata_difference"]

            explanation += f"Compared with Rank #{competitor_rank}, "

            # ----------------------------------------------------
            # Semantic comparison
            # ----------------------------------------------------

            if semantic_difference > 0.001:

                explanation += (
                    f"its semantic similarity was higher "
                    f"by {semantic_difference:.4f}. "
                )

            elif semantic_difference < -0.001:

                explanation += (
                    f"its semantic similarity was lower "
                    f"by {abs(semantic_difference):.4f}. "
                )

            else:

                explanation += "the semantic similarity was nearly equal. "

            # ----------------------------------------------------
            # Keyword comparison
            # ----------------------------------------------------

            if keyword_difference > 0.001:

                explanation += (
                    f"Its keyword overlap was also higher "
                    f"by {keyword_difference:.2f}. "
                )

            elif keyword_difference < -0.001:

                explanation += (
                    f"Its keyword overlap was lower "
                    f"by {abs(keyword_difference):.2f}. "
                )

            else:

                explanation += "Keyword overlap was nearly equal. "

            # ----------------------------------------------------
            # Metadata comparison
            # ----------------------------------------------------

            if metadata_difference > 0.001:

                explanation += "Its metadata was more relevant. "

            elif metadata_difference < -0.001:

                explanation += "Its metadata was less relevant. "

            else:

                explanation += "Metadata relevance was nearly equal. "

        # ========================================================
        # F3 CONFIDENCE
        # ========================================================

        explanation += (
            f"The retrieval confidence score is "
            f"{confidence_score:.3f}, classified as "
            f"{confidence_level}. "
        )

        # ========================================================
        # FINAL EXPLAINABILITY SCORE
        # ========================================================

        explanation += (
            f"The overall explainability score " f"is {explainability_score:.3f}."
        )

        return explanation

    # ============================================================
    # F3 — QUERY-LEVEL CONFIDENCE
    # ============================================================

    def _build_query_level_explanation(
        self, results, confidence_scores, explainability_scores, similarity_scores
    ):

        result_count = len(results)

        # --------------------------------------------------------
        # Similarity statistics
        # --------------------------------------------------------

        top_similarity = float(similarity_scores[0])

        if result_count > 1:

            second_similarity = float(similarity_scores[1])

            similarity_margin = top_similarity - second_similarity

        else:

            second_similarity = None
            similarity_margin = None

        average_similarity = sum(similarity_scores) / len(similarity_scores)

        average_explainability = sum(explainability_scores) / len(explainability_scores)

        # --------------------------------------------------------
        # Overall confidence
        #
        # Give the top result more importance because
        # it is the primary retrieval result.
        # --------------------------------------------------------

        if result_count == 1:

            overall_confidence = confidence_scores[0]

        else:

            top_confidence = confidence_scores[0]

            remaining_confidence = sum(confidence_scores[1:]) / len(
                confidence_scores[1:]
            )

            overall_confidence = 0.70 * top_confidence + 0.30 * remaining_confidence

        overall_confidence = max(0.0, min(1.0, overall_confidence))

        confidence_level = self._get_confidence_level(overall_confidence)

        # --------------------------------------------------------
        # Build query-level explanation
        # --------------------------------------------------------

        explanation = (
            f"The retrieval returned {result_count} results. "
            f"The top result has a cosine similarity of "
            f"{top_similarity:.4f}. "
        )

        if second_similarity is not None:

            explanation += (
                f"The second result has a cosine similarity "
                f"of {second_similarity:.4f}, giving a top-result "
                f"similarity margin of "
                f"{similarity_margin:.4f}. "
            )

        explanation += (
            f"The average similarity across retrieved results "
            f"is {average_similarity:.4f}. "
        )

        explanation += (
            f"The average explainability score is " f"{average_explainability:.3f}. "
        )

        explanation += (
            f"The overall retrieval confidence is "
            f"{overall_confidence:.3f}, classified as "
            f"{confidence_level}. "
        )

        # --------------------------------------------------------
        # Interpret confidence
        # --------------------------------------------------------

        if confidence_level == "HIGH":

            explanation += (
                "The retrieval is strongly supported by "
                "semantic relevance and supporting retrieval "
                "evidence."
            )

        elif confidence_level == "MEDIUM":

            explanation += (
                "The retrieval has reasonable support, but "
                "some retrieved results have weaker relevance "
                "or weaker separation from neighboring results."
            )

        else:

            explanation += (
                "The retrieval has limited confidence because "
                "semantic relevance or supporting evidence "
                "is relatively weak."
            )

        return {
            "overall_confidence_score": overall_confidence,
            "confidence_level": confidence_level,
            "result_count": result_count,
            "top_similarity": top_similarity,
            "second_similarity": second_similarity,
            "similarity_margin": similarity_margin,
            "average_similarity": average_similarity,
            "average_explainability": average_explainability,
            "explanation_text": explanation,
        }

    # ============================================================
    # READ RESULT-LEVEL EXPLANATIONS
    # ============================================================

    def get_query_explanations(self, query_id: int):

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        rr.result_id,
                        rr.rank,
                        rr.similarity_score,

                        d.title,
                        d.file_name,

                        c.chunk_id,
                        c.chunk_text,
                        c.page_number,
                        c.section_title,

                        e.explanation_id,
                        e.semantic_score,
                        e.keyword_score,
                        e.metadata_score,
                        e.ranking_score,
                        e.explainability_score,
                        e.confidence_score,
                        e.confidence_level,
                        e.explanation_text

                    FROM retrieval_results rr

                    JOIN chunks c
                        ON rr.chunk_id = c.chunk_id

                    JOIN documents d
                        ON c.document_id = d.document_id

                    LEFT JOIN explanations e
                        ON rr.result_id = e.result_id

                    WHERE rr.query_id = %s

                    ORDER BY rr.rank
                    """,
                    (query_id,),
                )

                return cursor.fetchall()

    # ============================================================
    # F3 — READ QUERY-LEVEL EXPLANATION
    # ============================================================

    def get_query_level_explanation(self, query_id: int):

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        query_explanation_id,
                        query_id,
                        overall_confidence_score,
                        confidence_level,
                        result_count,
                        top_similarity,
                        second_similarity,
                        similarity_margin,
                        average_similarity,
                        average_explainability,
                        explanation_text,
                        created_at
                    FROM query_explanations
                    WHERE query_id = %s
                    """,
                    (query_id,),
                )

                return cursor.fetchone()

    # ============================================================
    # F3 — READ CONFIDENCE SUMMARY
    # ============================================================

    def get_confidence_summary(self, query_id: int):

        query_level = self.get_query_level_explanation(query_id)

        result_level = self.get_query_explanations(query_id)

        return {
            "query": query_level,
            "results": [
                {
                    "result_id": row["result_id"],
                    "rank": row["rank"],
                    "similarity_score": row["similarity_score"],
                    "explainability_score": row["explainability_score"],
                    "confidence_score": row["confidence_score"],
                    "confidence_level": row["confidence_level"],
                }
                for row in result_level
            ],
        }

    # ============================================================
    # EXTRACT EVIDENCE SNIPPET
    # ============================================================

    def _extract_evidence_snippet(self, query_terms, chunk_text, max_length=250):

        if not chunk_text:
            return ""

        # --------------------------------------------------------
        # Split chunk into sentences.
        # --------------------------------------------------------

        sentences = re.split(r"(?<=[.!?])\s+", chunk_text)

        matching_sentences = []

        # --------------------------------------------------------
        # Find sentences containing query terms.
        # --------------------------------------------------------

        for sentence in sentences:

            sentence_terms = self._extract_terms(sentence)

            overlap = query_terms.intersection(sentence_terms)

            if overlap:

                matching_sentences.append(sentence.strip())

        # --------------------------------------------------------
        # If no matching sentence exists,
        # return beginning of chunk.
        # --------------------------------------------------------

        if not matching_sentences:

            return chunk_text[:max_length]

        # --------------------------------------------------------
        # Combine relevant sentences.
        # --------------------------------------------------------

        snippet = " ".join(matching_sentences)

        return snippet[:max_length]
