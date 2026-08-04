"""
tests/test_image_optimizer.py
"""

import io
import pytest
from PIL import Image
from backend.app.vision.image_optimizer import ImageResolutionOptimizer


@pytest.fixture
def large_test_image_bytes():
    """Generates a 3000x2000 test image in memory."""
    img = Image.new("RGB", (3000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=100)
    return buf.getvalue()


def test_image_optimizer_resizes_and_reduces_size(large_test_image_bytes):
    optimizer = ImageResolutionOptimizer(max_dimension=1024, quality=80)
    opt_bytes, meta = optimizer.optimize_image_bytes(large_test_image_bytes)

    # Assert dimension scaling
    assert meta["optimized_resolution"] == (1024, 682)
    
    # Assert payload size reduction
    assert meta["optimized_size_bytes"] < meta["original_size_bytes"]
    assert meta["reduction_percentage"] > 0


def test_small_image_bypasses_upscaling():
    """Ensures images smaller than max_dimension are not scaled up."""
    img = Image.new("RGB", (500, 400), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    small_bytes = buf.getvalue()

    optimizer = ImageResolutionOptimizer(max_dimension=1024)
    _, meta = optimizer.optimize_image_bytes(small_bytes)

    assert meta["optimized_resolution"] == (500, 400)