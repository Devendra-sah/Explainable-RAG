import re


class ChunkingService:

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        target_tokens=450,
        overlap_tokens=60,
        max_tokens=500
    ):
        self.model_name = model_name
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.max_tokens = max_tokens

        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        print("Tokenizer loaded successfully.")


    # --------------------------------------------------
    # Clean text
    # --------------------------------------------------

    def clean_text(self, text: str):
            if not text:
                return ""
    
            # Normalize line breaks
            text = text.replace("\r\n", "\n")
            text = text.replace("\r", "\n")
    
            # Normalize excessive whitespace
            text = re.sub(
                r"[ \t]+",
                " ",
                text
            )
    
            # Normalize excessive blank lines
            text = re.sub(
                r"\n{3,}",
                "\n\n",
                text
            )
    
            return text.strip()


    # --------------------------------------------------
    # Token count
    # --------------------------------------------------

    def count_tokens(self, text: str):

        if not text:
            return 0

        tokens = self.tokenizer.encode(
            text,
            add_special_tokens=False
        )

        return len(tokens)


    # --------------------------------------------------
    # Sentence splitting
    # --------------------------------------------------

    def split_sentences(self, text: str):

        text = self.clean_text(text)

        if not text:
            return []

        paragraphs = re.split(
            r"\n\s*\n",
            text
        )

        sentences = []

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            # Convert single line breaks inside a paragraph
            # into spaces while preserving word boundaries.
            paragraph = re.sub(
                r"(?<!\n)\n(?!\n)",
                " ",
                paragraph
            )

            paragraph_sentences = re.split(
                r"(?<=[.!?])\s+",
                paragraph
            )

            for sentence in paragraph_sentences:

                sentence = sentence.strip()

                if sentence:
                    sentences.append(sentence)

        return sentences


    # --------------------------------------------------
    # Split oversized sentence
    # --------------------------------------------------

    def split_large_text(self, text: str):

        words = text.split()

        pieces = []

        current_words = []

        current_token_count = 0

        for word in words:

            word_tokens = self.count_tokens(word)

            if (
                current_token_count + word_tokens
                > self.max_tokens
                and current_words
            ):

                pieces.append(
                    " ".join(current_words)
                )

                current_words = []
                current_token_count = 0

            current_words.append(word)
            current_token_count += word_tokens


        if current_words:

            pieces.append(
                " ".join(current_words)
            )

        return pieces


    # --------------------------------------------------
    # Create chunks
    # --------------------------------------------------

    def chunk_text(
        self,
        text: str,
        page_number=None,
        section_title=None
    ):

        sentences = self.split_sentences(text)

        processed_sentences = []

        for sentence in sentences:

            token_count = self.count_tokens(
                sentence
            )

            if token_count > self.max_tokens:

                pieces = self.split_large_text(
                    sentence
                )

                processed_sentences.extend(
                    pieces
                )

            else:

                processed_sentences.append(
                    sentence
                )


        chunks = []

        current_sentences = []
        current_tokens = 0


        for sentence in processed_sentences:

            sentence_tokens = self.count_tokens(
                sentence
            )


            # --------------------------------------
            # Start new chunk
            # --------------------------------------

            if (
                current_tokens + sentence_tokens
                > self.target_tokens
                and current_sentences
            ):

                chunk_text = " ".join(
                    current_sentences
                )

                chunks.append({
                    "text": chunk_text,
                    "page_number": page_number,
                    "section_title": section_title,
                    "token_count": self.count_tokens(
                        chunk_text
                    )
                })


                # ----------------------------------
                # Create token-aware overlap
                # ----------------------------------

                overlap_sentences = []
                overlap_tokens = 0

                # ----------------------------------
                # Create sentence-safe overlap
                # closest to target overlap
                # ----------------------------------

                candidate_sentences = []
                candidate_tokens = 0

                for previous_sentence in reversed(current_sentences):

                    previous_tokens = self.count_tokens(previous_sentence)

                    candidate_sentences.insert(
                        0,
                        previous_sentence
                    )

                    candidate_tokens += previous_tokens

                    # Once we pass the target, we have enough
                    # information to compare the current suffix
                    # with the previous suffix.
                    if candidate_tokens >= self.overlap_tokens:

                        # Calculate the suffix without the
                        # most recently added sentence.
                        previous_sentences = candidate_sentences[1:]

                        previous_tokens = (
                            candidate_tokens
                            - previous_tokens
                        )

                        # Choose whichever is closer to the
                        # requested overlap.
                        if (
                            previous_sentences
                            and abs(
                                previous_tokens
                                - self.overlap_tokens
                            )
                            <= abs(
                                candidate_tokens
                                - self.overlap_tokens
                            )
                        ):
                            overlap_sentences = previous_sentences
                            overlap_tokens = previous_tokens

                        else:
                            overlap_sentences = candidate_sentences
                            overlap_tokens = candidate_tokens

                        break

                else:

                    overlap_sentences = candidate_sentences
                    overlap_tokens = candidate_tokens

                current_sentences = overlap_sentences

                current_tokens = overlap_tokens


            current_sentences.append(
                sentence
            )

            current_tokens += sentence_tokens


        # ------------------------------------------
        # Final chunk
        # ------------------------------------------

        if current_sentences:

            chunk_text = " ".join(
                current_sentences
            )

            chunks.append({
                "text": chunk_text,
                "page_number": page_number,
                "section_title": section_title,
                "token_count": self.count_tokens(
                    chunk_text
                )
            })


        return chunks