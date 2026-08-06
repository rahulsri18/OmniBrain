"""
backend/app/vision/embedder.py
Optimized Image Embedding Loader with FP16 Precision, Lazy Loading & RAM Offloading.
"""

import gc
import logging
from typing import Optional

import torch
from PIL import Image

logger = logging.getLogger(__name__)


class OptimizedVisionEmbedder:
    _instance: Optional["OptimizedVisionEmbedder"] = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to avoid loading duplicate model instances in RAM."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "openai"):
        if self._initialized:
            return

        self.model_name = model_name
        self.pretrained = pretrained
        self.model = None
        self.preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialized = True
        logger.info(
            f"VisionEmbedder initialized in Lazy mode for device: {self.device}"
        )

    def _load_model(self):
        """Lazy loader: Loads model only when first embedding request arrives."""
        if self.model is not None:
            return

        logger.info(
            "Loading CLIP model into memory with FP16 / Half Precision optimization..."
        )

        try:
            import open_clip

            # 1. Load model with half-precision (FP16) on GPU or CPU if supported
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.model_name,
                pretrained=self.pretrained,
                precision="fp16" if self.device == "cuda" else "fp32",
                device=self.device,
            )

            # 2. Apply Dynamic Quantization for CPU Execution to save RAM
            if self.device == "cpu":
                model = torch.quantization.quantize_dynamic(
                    model, {torch.nn.Linear}, dtype=torch.qint8
                )

            model.eval()
            self.model = model
            self.preprocess = preprocess
            logger.info("CLIP model loaded successfully into optimized memory space.")

        except Exception as e:
            logger.error(f"Failed to load vision embedder: {e!s}")
            raise # Bare raise preserves the stack trace

    @torch.inference_mode()
    def embed_image(self, image_input: Image.Image) -> list[float]:
        """Generates embedding for a PIL Image using minimal memory footprint."""
        self._load_model()

        if image_input.mode != "RGB":
            image_input = image_input.convert("RGB")

        # Process single image tensor
        image_tensor = self.preprocess(image_input).unsqueeze(0).to(self.device)

        # FP16 Auto-cast block
        if self.device == "cuda":
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                image_features = self.model.encode_image(image_tensor)
        else:
            image_features = self.model.encode_image(image_tensor)

        # Normalize features
        image_features /= image_features.norm(dim=-1, keepdim=True)
        embedding = image_features.cpu().numpy().flatten().tolist()

        # Clean intermediate Tensors from cache
        del image_tensor, image_features
        return embedding

    def unload_model(self):
        """Manual Memory Offloader: Call during low activity or long idle times."""
        if self.model is not None:
            logger.info("Unloading CLIP model from RAM/VRAM to free resources...")
            del self.model
            del self.preprocess
            self.model = None
            self.preprocess = None

            # Force Python Garbage Collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("RAM successfully reclaimed.")
