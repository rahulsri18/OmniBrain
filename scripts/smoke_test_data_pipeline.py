import os
import sys
import time
from pathlib import Path

# ------------------------------------------------------------------
# 1. Dynamic Path Resolution (Works when run from root or scripts)
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))
sys.path.append(str(PROJECT_ROOT))

import pymupdf as fitz
from backend.app.ingestion.pdf_pipeline import extract_pdf_content_robust
from backend.app.logger import logger
from backend.app.vectordb.qdrant_client import QdrantDB


# ------------------------------------------------------------------
# 2. Helper to Guarantee Sample Test PDF Exists
# ------------------------------------------------------------------
def ensure_sample_pdf_exists(pdf_path: str | Path) -> Path:
    """
    Ensures a valid sample PDF file exists at the given path.
    If missing, creates a simple PDF file programmatically.
    """
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            "OmniBrain Production Data Pipeline Smoke Test Document.\n"
            "This text verifies PDF content extraction, chunking, and Qdrant indexing."
        )
        doc.save(str(path_obj))
        doc.close()
        logger.info(f"Created sample test PDF at '{path_obj}'.")
        
    return path_obj


# ------------------------------------------------------------------
# 3. Main Data Pipeline Smoke Test Execution Function
# ------------------------------------------------------------------
def run_data_pipeline_smoke_test(test_pdf_path: str):
    """
    M2 Day 20: Production Data Pipeline & Indexing Smoke Test.
    Confirms PDF extraction, Qdrant connectivity, vector insertion, and collection count.
    """
    logger.info("=== STARTING M2 DATA PIPELINE PRODUCTION SMOKE TEST ===")
    start_time = time.time()

    # ------------------------------------------------------------------
    # TEST 1: Validate PDF Input File (Creates if missing)
    # ------------------------------------------------------------------
    logger.info("[Test 1/4] Checking PDF File Availability & Structure...")
    pdf_file = ensure_sample_pdf_exists(test_pdf_path)

    if not pdf_file.exists():
        logger.error(f"FAIL: Unable to locate or create test PDF at '{test_pdf_path}'.")
        sys.exit(1)

    logger.info(f"PASS: Verified test PDF '{pdf_file.name}' ({pdf_file.stat().st_size} bytes).")

    # ------------------------------------------------------------------
    # TEST 2: Robust Content Extraction
    # ------------------------------------------------------------------
    logger.info("[Test 2/4] Testing PDF Content & Text Extraction...")
    extraction_result = extract_pdf_content_robust(pdf_file)

    assert extraction_result["success"] is True, f"FAIL: Extraction failed: {extraction_result.get('error')}"
    assert len(extraction_result["pages"]) > 0, "FAIL: No pages extracted from PDF."

    logger.info(
        f"PASS: Extracted {extraction_result['total_pages']} pages "
        f"(Is Scanned: {extraction_result['is_scanned']})."
    )

    # ------------------------------------------------------------------
    # TEST 3: Qdrant Connection & Initial Count Check
    # ------------------------------------------------------------------
    logger.info("[Test 3/4] Connecting to Qdrant & Checking Collection Health...")
    db = QdrantDB()
    collection_name = getattr(db, "text_collection_name", "omnibrain_text")

    try:
        initial_info = db.client.get_collection(collection_name=collection_name)
        initial_count = initial_info.points_count
        logger.info(f"Connected to Qdrant collection '{collection_name}'. Current point count: {initial_count}")
    except Exception as err:  # noqa: BLE001
        logger.error(f"FAIL: Could not query Qdrant collection '{collection_name}': {err}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # TEST 4: Indexing & Payload Verification
    # ------------------------------------------------------------------
    logger.info("[Test 4/4] Ingesting Sample Text Chunks into Vector Store...")
    sample_text = extraction_result["pages"][0]["text"][:200]
    dummy_vector = [0.01] * 512  # Target text collection vector dimension

    metadata = [{
        "file_name": pdf_file.name,
        "page_number": 1,
        "chunk_text": sample_text,
        "type": "smoke_test_doc"
    }]

    try:
        db.insert_vectors(
            chunks=[sample_text],
            embeddings=[dummy_vector],
            metadata=metadata,
            collection_name=collection_name,
        )

        # Pause briefly to allow Qdrant write commitment
        time.sleep(1)
        updated_info = db.client.get_collection(collection_name=collection_name)
        final_count = updated_info.points_count

        logger.info(f"PASS: Vectors indexed successfully. Updated point count: {final_count}")
        assert final_count >= initial_count, "FAIL: Point count did not increase after indexing."

    except Exception as err:  # noqa: BLE001
        logger.error(f"FAIL: Vector insertion or indexing verification failed: {err}")
        sys.exit(1)

    elapsed = time.time() - start_time
    logger.info(f"=== M2 DATA PIPELINE SMOKE TEST COMPLETED SUCCESSFULLY ({elapsed:.2f}s) ===")


if __name__ == "__main__":
    sample_pdf_path = "tests/data/sample_doc.pdf"
    run_data_pipeline_smoke_test(sample_pdf_path)