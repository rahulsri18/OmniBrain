# scripts/test_pdf_edge_cases.py

from app.ingestion.pdf_pipeline import extract_pdf_content_robust
from app.logger import logger

def test_pdf_pipeline():
    logger.info("=== STARTING M2 DAY 19 PDF PIPELINE TEST ===")
    
    # Path to test PDF file
    test_pdf = "tests/data/sample_edge_case.pdf"
    
    result = extract_pdf_content_robust(test_pdf)
    
    assert result["success"] is True, f"Pipeline failed: {result.get('error')}"
    logger.info(f"Success! Total Pages: {result['total_pages']}, Is Scanned: {result['is_scanned']}")

if __name__ == "__main__":
    test_pdf_pipeline()