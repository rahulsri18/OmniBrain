"""
backend/services/vision_optimizer.py
M4 Day 16: Vision Model Quantization & Batch Inference Engine
"""

from typing import List, Dict, Any, Union
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq, BitsAndBytesConfig


class OptimizedVisionInferenceEngine:
    """
    Manages quantized vision model loading (8-bit / 4-bit) and batch processing 
    to maximize inference throughput and reduce memory footprint.
    """

    def __init__(
        self,
        model_id: str = "Salesforce/blip2-opt-2.7b",
        load_in_8bit: bool = True,
        device: str = None,
    ):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.load_in_8bit = load_in_8bit and (self.device == "cuda")

        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads vision processor and model with optional INT8 quantization."""
        print(f"[M4 Vision Engine] Loading processor for {self.model_id}...")
        self.processor = AutoProcessor.from_pretrained(self.model_id)

        if self.load_in_8bit:
            print(f"[M4 Vision Engine] Applying INT8 Quantization via bitsandbytes...")
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
            )
            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_id,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
            )
        else:
            print(f"[M4 Vision Engine] Loading model in default fp16/fp32 mode...")
            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            ).to(self.device)

        self.model.eval()

    @torch.inference_mode()
    def process_image_batch(
        self,
        images: List[Image.Image],
        prompts: List[str] = None,
        max_new_tokens: int = 50,
    ) -> List[str]:
        """
        Executes batch inference over multiple images simultaneously to increase CPU/GPU throughput.

        Args:
            images: List of PIL images to analyze.
            prompts: Optional list of prompt strings corresponding to each image.
            max_new_tokens: Maximum response tokens per image.

        Returns:
            List[str]: Model response texts for each image in the batch.
        """
        if not images:
            return []

        if prompts is None:
            prompts = ["a photo of"] * len(images)

        # Batch preprocessing
        inputs = self.processor(
            images=images,
            text=prompts,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        if self.load_in_8bit or self.device == "cuda":
            inputs = {
                k: v.to(torch.float16) if v.dtype == torch.float32 else v
                for k, v in inputs.items()
            }

        # Batched inference pass
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
        )

        # Batch decoding
        decoded_responses = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )

        return [res.strip() for res in decoded_responses]