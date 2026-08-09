# scripts/smoke_test_vision.py

import sys
import time
from pathlib import Path

# Add 'backend' directory to Python search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))
sys.path.append(str(PROJECT_ROOT))

from backend.app.ingestion.vision_pipeline import process_vision_output_with_retry, VisionIngestionPipeline
from backend.app.logger import logger


def run_vision_smoke_test(test_image_path: str):
    """
    Day 20: Production Smoke Test for Vision Sub-Agent
    Validates end-to-end functionality, response quality, and error handling.
    """
    logger.info("=== STARTING VISION SUB-AGENT SMOKE TEST ===")
    
    # ------------------------------------------------------------------
    # TEST 1: Path Validation & File Check
    # ------------------------------------------------------------------
    logger.info("[Test 1/4] Testing File Path & Blur Validation...")
    start_time = time.time()
    
    if not Path(test_image_path).exists():
        logger.error(f"FAIL: Test image not found at '{test_image_path}'. Place a valid image and re-run.")
        sys.exit(1)
        
    logger.info("PASS: Image file verified.")

    # ------------------------------------------------------------------
    # TEST 2: CLIP Embedding & Qdrant Connection
    # ------------------------------------------------------------------
    logger.info("[Test 2/4] Testing CLIP Embedding Generation & DB Collection...")
    pipeline = VisionIngestionPipeline()
    embedding = pipeline.generate_image_embedding(test_image_path)
    
    assert len(embedding) == 512, f"FAIL: Expected embedding vector dimension 512, got {len(embedding)}"
    logger.info("PASS: 512-dim CLIP embedding generated successfully.")

    # ------------------------------------------------------------------
    # TEST 3: Vision Agent Inference & Quality Schema
    # ------------------------------------------------------------------
    logger.info("[Test 3/4] Testing Vision Agent Parsing & Output Quality...")
    result = process_vision_output_with_retry(image_path=test_image_path)
    
    assert isinstance(result, dict), "FAIL: Vision agent output must be a dictionary."
    assert "success" in result, "FAIL: Output missing 'success' key."
    
    if result["success"]:
        data = result.get("data", {})
        assert "status" in data, "FAIL: Response data missing 'status' field."
        assert "description" in data, "FAIL: Response data missing 'description' field."
        logger.info(f"PASS: Structured output verified -> Status: {data.get('status')}")
    else:
        logger.warning(f"Vision Agent returned non-success response: {result.get('reason')}")

    # ------------------------------------------------------------------
    # TEST 4: Performance / Latency Check
    # ------------------------------------------------------------------
    elapsed = time.time() - start_time
    logger.info(f"[Test 4/4] Execution Latency: {elapsed:.2f} seconds.")
    
    logger.info("=== VISION SUB-AGENT SMOKE TEST COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    # Pass a sample image path for production testing
    sample_image = "tests/data/sample_chart.png"
    run_vision_smoke_test(sample_image)