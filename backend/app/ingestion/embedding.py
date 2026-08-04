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
        batch_size: int = 32,
    ):
        self.model = SentenceTransformer(model_name)
        # Configurable rather than hardcoded so callers can tune throughput
        # vs. memory (larger batches = fewer model invocations but more
        # memory per call) without touching this file. Can still be
        # overridden per-call via generate_embeddings(batch_size=...).
        self.batch_size = batch_size

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
        batch_size: int = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple chunks in batches, instead of one
        model call per chunk. For 1000 chunks with batch_size=32, this
        results in ~32 model invocations instead of 1000.
 
        `batch_size` overrides the instance default (self.batch_size) for
        this call only -- useful for tuning per-document without mutating
        shared state on the generator.
 
        Empty/whitespace-only chunks are skipped before encoding (matching
        generate_embedding()'s behavior of returning [] for empty text) and
        an empty list is reinserted at their original position, so the
        output list is always the same length as the input list and index
        i of the result always corresponds to index i of `chunks`.
        """
 
        if not chunks:
            return []
 
        effective_batch_size = batch_size if batch_size is not None else self.batch_size
        if effective_batch_size < 1:
            raise ValueError("batch_size must be >= 1")
 
        # Separate valid chunks from empty ones, but remember original
        # positions so we can reinsert [] placeholders and preserve
        # index-to-index correspondence with the input.
        valid_indices = []
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk and chunk.strip():
                valid_indices.append(i)
                valid_chunks.append(chunk)
 
        results: List[List[float]] = [[] for _ in chunks]
        