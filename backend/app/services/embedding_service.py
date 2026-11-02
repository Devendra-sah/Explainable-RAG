class EmbeddingService:
    _shared_model = None

    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"

        self._model = None

    @property
    def model(self):
        if EmbeddingService._shared_model is None:
            from sentence_transformers import SentenceTransformer

            print(f"Loading embedding model: {self.model_name}")
            EmbeddingService._shared_model = SentenceTransformer(self.model_name)
            print("Embedding model loaded successfully.")
        self._model = EmbeddingService._shared_model
        return EmbeddingService._shared_model

    def generate_embedding(self, text: str):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

    def get_dimension(self):

        return self.model.get_sentence_embedding_dimension()