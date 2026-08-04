"""
backend/api/v1/vision.py
M4 Day 16: API Endpoint consuming Quantized & Batched Vision Engine
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from PIL import Image
import io

# pyrefly: ignore [missing-import]
from backend.services.vision_optimizer import OptimizedVisionInferenceEngine

router = APIRouter(prefix="/api/v1/vision", tags=["Vision Agent"])

# Instantiate optimized vision engine singleton
vision_engine = OptimizedVisionInferenceEngine(load_in_8bit=True)


@router.post("/batch-analyze")
async def analyze_batch_images(
    files: List[UploadFile] = File(...),
    prompt: str = "Describe this document visual or diagram in detail.",
):
    """Batch processes uploaded images using 8-bit quantized vision model."""
    if not files:
        raise HTTPException(status_code=400, detail="No images provided for batching.")

    try:
        pil_images = []
        for file in files:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents)).convert("RGB")
            pil_images.append(img)

        prompts = [prompt] * len(pil_images)

        # Perform batched inference
        results = vision_engine.process_image_batch(
            images=pil_images,
            prompts=prompts,
            max_new_tokens=100,
        )

        return {
            "batch_size": len(pil_images),
            "quantized_8bit": vision_engine.load_in_8bit,
            "results": [
                {"filename": file.filename, "description": res}
                for file, res in zip(files, results)
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch vision error: {str(e)}")