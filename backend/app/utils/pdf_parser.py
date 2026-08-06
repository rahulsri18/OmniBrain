"""
pdf_parser.py

Utility functions for extracting text, tables, and metadata from PDF files.
"""

from pathlib import Path
from pydoc import text
import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError


class PDFParser:
    """
    Utility class for parsing PDF documents.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        if self.pdf_path.stat().st_size == 0:
            raise ValueError("Uploaded PDF is empty.")

    # Validate the PDF during initialization
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                _ = len(pdf.pages)
        except PDFPasswordIncorrect:
            raise ValueError(
            "Password-protected PDFs are not supported."
        )
        except PDFSyntaxError:
            raise ValueError(
            "The PDF is corrupted or has an invalid format."
        )
        except Exception as e:
            raise ValueError(
            f"Unable to open PDF: {e}"
        )

    def extract_text(self) -> str:
        """
          Extract complete text from the PDF.
        """

        text = ""

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

        except Exception as e:
            raise ValueError(f"Failed to extract text: {e}")

        return text.strip()

    
    def extract_pagewise_text(self):
        pages = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    pages.append(
                        {
                            "page": index,
                            "text": page.extract_text() or ""
                        }
                    )
        except Exception as e:
            raise ValueError(f"Failed to extract page-wise text: {e}")

        return pages

    def extract_tables(self):
        """
        Extract tables from every page.
        """

        all_tables = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):

                tables = page.extract_tables()

                if tables:
                    all_tables.append(
                        {
                            "page": index,
                            "tables": tables
                        }
                    )

        return all_tables

    def get_metadata(self):
        """
        Return PDF metadata.
        """

        with pdfplumber.open(self.pdf_path) as pdf:

            return {
                "file_name": self.pdf_path.name,
                "total_pages": len(pdf.pages),
                "metadata": pdf.metadata,
            }