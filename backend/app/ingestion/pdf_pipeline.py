# backend/app/ingestion/pdf_pipeline.py

import os
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from app.logger import logger


def validate_pdf_file(pdf_path: str | Path) -> Path:
    """
    Validates that the file exists, is non-empty, and is a valid PDF header.
    Fixes bug bash issue: Prevents pipeline crashes on corrupted/truncated PDFs.
    """
    path_obj = Path(pdf_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    if path_obj.stat().st_size == 0:
        raise ValueError(f"PDF file at '{pdf_path}' is empty (0 bytes).")

    # Read the first 5 bytes to verify PDF header (%PDF-)
    with open(path_obj, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise ValueError(f"File at '{pdf_path}' is not a valid PDF document (invalid header).")

    return path_obj


def extract_pdf_content_robust(pdf_path: str | Path) -> dict[str, Any]:
    """
    Edge-Case Resistant PDF Parser (M2 Day 19 Fix).
    
    Handles:
    1. Scanned/Image-only PDFs (Flags for OCR fallback if text length < threshold).
    2. Password-protected / Encrypted PDFs (Attempts blank-password unlock).
    3. Multi-column layout text extraction using layout sorting.
    4. Damaged/Corrupted page streams.
    """
    try:
        valid_path = validate_pdf_file(pdf_path)
    except (FileNotFoundError, ValueError) as err:
        logger.error(f"PDF Validation failed for '{pdf_path}': {err}")
        return {
            "success": False,
            "reason": "invalid_pdf_file",
            "error": str(err),
            "pages": [],
        }

    extracted_pages = []
    is_scanned_doc = True  # Default assume scanned until text is found

    try:
        doc = fitz.open(valid_path)

        # Handle Password / Encryption Edge Case
        if doc.is_encrypted:
            logger.warning(f"PDF '{valid_path.name}' is encrypted. Attempting default authentication...")
            unlocked = doc.authenticate("")
            if not unlocked:
                logger.error(f"Failed to unlock encrypted PDF '{valid_path.name}'.")
                return {
                    "success": False,
                    "reason": "encrypted_pdf_locked",
                    "error": "Password required to extract PDF content.",
                    "pages": [],
                }

        for page_num in range(len(doc)):
            try:
                page = doc[page_num]

                # Extract text using 'blocks' mode to maintain proper reading order for multi-column pages
                blocks = page.get_text("blocks", flags=fitz.TEXT_DEHYPHENATE)
                
                # Sort blocks vertically, then horizontally (Layout Fix)
                blocks.sort(key=lambda b: (b[1], b[0]))
                
                page_text = "\n".join([b[4].strip() for b in blocks if b[4].strip()])

                # Check if page actually contains extractable text
                if len(page_text.strip()) > 50:
                    is_scanned_doc = False

                extracted_pages.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "char_count": len(page_text),
                })

            except Exception as page_err:  # noqa: BLE001
                logger.warning(f"Error processing page {page_num + 1} of '{valid_path.name}': {page_err}")
                extracted_pages.append({
                    "page_number": page_num + 1,
                    "text": "",
                    "error": str(page_err),
                })

        doc.close()

        # Scanned Image-only PDF Detection Edge Case
        if is_scanned_doc:
            logger.warning(
                f"PDF '{valid_path.name}' appears to be a scanned image-only PDF. "
                "Text extraction yielded minimal content; routing to OCR ingestion."
            )

        return {
            "success": True,
            "file_name": valid_path.name,
            "total_pages": len(extracted_pages),
            "is_scanned": is_scanned_doc,
            "pages": extracted_pages,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error(f"Catastrophic failure parsing PDF '{pdf_path}': {exc}")
        return {
            "success": False,
            "reason": "pdf_parsing_failure",
            "error": str(exc),
            "pages": [],
        }