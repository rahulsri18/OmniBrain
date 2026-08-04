"""
tests/test_vision_optimizer.py
M4 Day 16: Verification unit test for Quantization & Batch Vision Inference
"""

import pytest
from PIL import Image
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
from backend.services.vision_optimizer import OptimizedVisionInferenceEngine


@pytest.fixture
def sample_images():
    """Generates 3 synthetic RGB images for batching tests."""
    return [
        Image.new("RGB", (100, 100), color="red"),
        Image.new("RGB", (100, 100), color="blue"),
        Image.new("RGB", (100, 100), color="green"),
    ]


@patch("backend.services.vision_optimizer.AutoModelForVision2Seq")
@patch("backend.services.vision_optimizer.AutoProcessor")
def test_batch_vision_processing(mock_processor, mock_model, sample_images):
    """Verifies batch inference engine formats input and decodes output properly."""

    # Mock Processor & Model behavior
    mock_proc_instance = MagicMock()
    mock_proc_instance.return_value.to.return_value = {"pixel_values": None}
    mock_proc_instance.batch_decode.return_value = [
        "Red square",
        "Blue square",
        "Green square",
    ]
    mock_processor.from_pretrained.return_value = mock_proc_instance

    mock_model_instance = MagicMock()
    mock_model.from_pretrained.return_value = mock_model_instance

    # Initialize Engine in CPU fallback mode for test
    engine = OptimizedVisionInferenceEngine(load_in_8bit=False, device="cpu")

    results = engine.process_image_batch(images=sample_images)

    assert len(results) == 3
    assert results[0] == "Red square"
    assert results[1] == "Blue square"
    assert results[2] == "Green square"