"""
app/vision/image_optimizer.py

Optimizes image resolution and payload size before sending to vision models.
Reduces token cost and sub-agent response latency.
"""

import io
import base64
from typing import Tuple, Union
from PIL import Image


class ImageResolutionOptimizer:
    """Handles image preprocessing, smart resizing, and compression."""

    def __init__(
        self,
        max_dimension: int = 1024,
        quality: int = 85,
        max_payload_bytes: int = 2 * 1024 * 1024  # 2MB
    ):
        """
        :param max_dimension: Maximum width or height in pixels.
        :param quality: JPEG compression quality (1-100).
        :param max_payload_bytes: Preferred maximum byte size threshold.
        """
        self.max_dimension = max_dimension
        self.quality = quality
        self.max_payload_bytes = max_payload_bytes

    def optimize_image_bytes(self, image_bytes: bytes) -> Tuple[bytes, dict]:
        """
        Processes raw image bytes and returns optimized bytes with performance metadata.
        """
        img = Image.open(io.BytesIO(image_bytes))
        orig_width, orig_height = img.size
        orig_size = len(image_bytes)

        # Convert palette/RGBA modes to RGB for JPEG formatting
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # 1. Calculate aspect-preserving dimensions
        new_width, new_height = self._calculate_dimensions(orig_width, orig_height)

        # 2. Resize only if dimensions exceed max threshold
        if (new_width, new_height) != (orig_width, orig_height):
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 3. Compress to JPEG in-memory stream
        output_stream = io.BytesIO()
        img.save(output_stream, format="JPEG", quality=self.quality, optimize=True)
        optimized_bytes = output_stream.getvalue()
        optimized_size = len(optimized_bytes)

        metadata = {
            "original_resolution": (orig_width, orig_height),
            "optimized_resolution": (new_width, new_height),
            "original_size_bytes": orig_size,
            "optimized_size_bytes": optimized_size,
            "reduction_percentage": round((1 - (optimized_size / orig_size)) * 100, 2)
            if orig_size > 0
            else 0,
        }

        return optimized_bytes, metadata

    def optimize_to_base64(self, image_bytes: bytes) -> Tuple[str, dict]:
        """Convenience method returning base64-encoded optimized image."""
        opt_bytes, meta = self.optimize_image_bytes(image_bytes)
        b64_str = base64.b64encode(opt_bytes).decode("utf-8")
        return b64_str, meta

    def _calculate_dimensions(self, width: int, height: int) -> Tuple[int, int]:
        """Scales down width/height proportionally if either exceeds max_dimension."""
        if width <= self.max_dimension and height <= self.max_dimension:
            return width, height

        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))

        return new_width, new_height