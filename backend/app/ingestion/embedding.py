"""
embedding.py

Generate embeddings using the all-MiniLM-L6-v2 model.
"""

from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    Generate vector embeddings for text chunks.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.
        """

        if not text.strip():
            return []

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def generate_embeddings(
        self,
        chunks: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple chunks.
        """

        if not chunks:
            return []

        embeddings = self.model.encode(
            chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()