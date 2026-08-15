"""
image_filter.py

Utility to evaluate and filter out low-quality, icon-sized, 
or blank images during the vision parsing pipeline.
"""

import os
from io import BytesIO
from PIL import Image, ImageStat
from app.logger import logger


class ImageQualityFilter:
    def __init__(
        self,
        min_width: int = 150,
        min_height: int = 150,
        min_file_size_bytes: int = 5000,  # ~5 KB
        max_aspect_ratio: float = 5.0
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.min_file_size_bytes = min_file_size_bytes
        self.max_aspect_ratio = max_aspect_ratio

    def is_blank_or_solid_color(self, img: Image.Image, std_dev_threshold: float = 10.0) -> bool:
        try:
            grayscale_img = img.convert("L")
            stat = ImageStat.Stat(grayscale_img)
            std_dev = stat.stddev[0]
            
            return std_dev < std_dev_threshold
        except Exception as e:
            logger.warning(f"Failed to check image color variance: {e}")
            return False

    def is_high_quality(self, image_bytes: bytes) -> bool:
        if len(image_bytes) < self.min_file_size_bytes:
            logger.debug(f"Image filtered out: File size too small ({len(image_bytes)} bytes)")
            return False

        try:
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size

            if width < self.min_width or height < self.min_height:
                logger.debug(f"Image filtered out: Resolution too low ({width}x{height})")
                return False

            aspect_ratio = max(width / height, height / width)
            if aspect_ratio > self.max_aspect_ratio:
                logger.debug(f"Image filtered out: Aspect ratio too extreme ({aspect_ratio:.2f})")
                return False

            if self.is_blank_or_solid_color(img):
                logger.debug("Image filtered out: Image is blank or solid color")
                return False

            return True

        except Exception as e:
            logger.error(f"Error parsing image bytes during quality check: {e}")
            return False


# Global Singleton Instance for easy usage across vision modules
image_quality_filter = ImageQualityFilter()