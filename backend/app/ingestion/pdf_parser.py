# app/ingestion/pdf_parser.py

import logging
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger("omnibrain.m1.parser")


class PDFParser:
    """Extracts raw text and structural metadata from PDF documents."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Target PDF file not found at: {self.file_path}")

    def extract_text(self) -> list[dict[str, Any]]:
        """Extracts text page-by-page with page-number metadata."""
        pages_data: list[dict[str, Any]] = []

        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    extracted_text = page.extract_text() or ""
                    if extracted_text.strip():
                        pages_data.append(
                            {
                                "page_number": page_num,
                                "content": extracted_text.strip(),
                                "char_count": len(extracted_text),
                            }
                        )
            logger.info(
                f"Successfully parsed {len(pages_data)} pages from {self.file_path.name}"
            )
            return pages_data

        except Exception as e:
            logger.error(f"Failed to extract text from {self.file_path.name}: {e!s}")
            raise RuntimeError(
                f"PDF Parsing error on {self.file_path.name}: {e!s}"
            ) from e
