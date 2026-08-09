"""
tests/test_embedding_batching.py
M2 Day 16: Unit tests for batch embedding generation logic
"""

import pytest
from backend.app.ingestion.embedding import EmbeddingGenerator


@pytest.fixture
def embedding_generator():
    return EmbeddingGenerator(batch_size=4)


def test_generate_embeddings_batch_indexing(embedding_generator):
    """Verify output length matches input length and handles empty strings gracefully."""
    chunks = [
        "First document chunk about machine learning.",
        "",  # Empty chunk
        "Second valid chunk discussing vector databases.",
        "   ",  # Whitespace-only chunk
        "Third valid chunk regarding retrieval augmented generation.",
    ]

    embeddings = embedding_generator.generate_embeddings(chunks, batch_size=2)

    # Output length must strictly equal input length
    assert len(embeddings) == len(chunks)

    # Valid chunks must produce non-empty vector lists
    assert len(embeddings[0]) > 0
    assert len(embeddings[2]) > 0
    assert len(embeddings[4]) > 0

    # Empty/whitespace chunks must preserve empty list placeholders
    assert embeddings[1] == []
    assert embeddings[3] == []


def test_generate_embeddings_empty_input(embedding_generator):
    """Verify empty input returns empty list."""
    assert embedding_generator.generate_embeddings([]) == []


def test_invalid_batch_size(embedding_generator):
    """Verify error raised on invalid batch size."""
    with pytest.raises(ValueError, match="batch_size must be >= 1"):
        embedding_generator.generate_embeddings(["Sample text"], batch_size=0)