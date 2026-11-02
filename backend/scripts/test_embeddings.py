from app.services.embedding_service import EmbeddingService


service = EmbeddingService()


text = """
Database normalization is a database design technique
used to reduce data redundancy and improve data integrity.
"""


embedding = service.generate_embedding(text)


print("\nEmbedding generated successfully.")

print("Dimension:", len(embedding))

print("First 10 values:")

print(embedding[:10])