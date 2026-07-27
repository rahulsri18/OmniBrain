"""
tests/test_vision_embedder.py
Unit tests verifying Lazy Loading and Unload Behavior.
"""

import pytest
from PIL import Image
from backend.app.ingestion.vision_embedder import OptimizedVisionEmbedder


def test_lazy_loading_behavior():
    embedder = OptimizedVisionEmbedder()
    # Verify model is NOT loaded on instantiation
    assert embedder.model is None

    # Dummy image
    img = Image.new("RGB", (224, 224), color="red")
    
    # Model should load on first invocation
    vector = embedder.embed_image(img)
    
    assert embedder.model is not None
    assert isinstance(vector, list)
    assert len(vector) > 0


def test_unload_memory():
    embedder = OptimizedVisionEmbedder()
    img = Image.new("RGB", (224, 224), color="blue")
    
    embedder.embed_image(img)
    assert embedder.model is not None

    # Unload model & verify memory cleanup
    embedder.unload_model()
    assert embedder.model is None