"""
tests/test_vision_optimizer.py

M4 Day 16:
Verification unit test for Quantization & Batch Vision Inference
"""

import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from backend.app.services.vision_optimizer import (
    OptimizedVisionInferenceEngine,
)


@pytest.fixture
def sample_images():
    """Generate three synthetic RGB images."""
    return [
        Image.new("RGB", (100, 100), "red"),
        Image.new("RGB", (100, 100), "blue"),
        Image.new("RGB", (100, 100), "green"),
    ]


@patch("backend.app.services.vision_optimizer.AutoModelForVision2Seq")
@patch("backend.app.services.vision_optimizer.AutoProcessor")
def test_batch_vision_processing(
    mock_processor,
    mock_model,
    sample_images,
):
    """Verify batch inference returns decoded outputs."""

    processor = MagicMock()

    processor.return_value.to.return_value = {
        "pixel_values": None
    }

    processor.batch_decode.return_value = [
        "Red square",
        "Blue square",
        "Green square",
    ]

    mock_processor.from_pretrained.return_value = processor

    model = MagicMock()

    mock_model.from_pretrained.return_value = model

    engine = OptimizedVisionInferenceEngine(
        load_in_8bit=False,
        device="cpu",
    )

    results = engine.process_image_batch(sample_images)

    assert len(results) == 3
    assert results == [
        "Red square",
        "Blue square",
        "Green square",
    ]