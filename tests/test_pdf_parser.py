import pytest
from unittest.mock import MagicMock, patch

from backend.app.utils.pdf_parser import PDFParser


# ============================================================
# Constructor
# ============================================================

def test_pdf_not_found():
    with pytest.raises(FileNotFoundError):
        PDFParser("missing.pdf")


# ============================================================
# extract_text
# ============================================================

@patch("backend.app.utils.pdf_parser.pdfplumber.open")
def test_extract_text(mock_open, tmp_path):

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy")

    page1 = MagicMock()
    page1.extract_text.return_value = "Hello"

    page2 = MagicMock()
    page2.extract_text.return_value = "World"

    pdf = MagicMock()
    pdf.pages = [page1, page2]

    mock_open.return_value.__enter__.return_value = pdf

    parser = PDFParser(str(pdf_file))

    text = parser.extract_text()

    assert text == "Hello\nWorld"


# ============================================================
# extract_empty_text
# ============================================================

@patch("backend.app.utils.pdf_parser.pdfplumber.open")
def test_extract_empty_text(mock_open, tmp_path):

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy")

    page = MagicMock()
    page.extract_text.return_value = None

    pdf = MagicMock()
    pdf.pages = [page]

    mock_open.return_value.__enter__.return_value = pdf

    parser = PDFParser(str(pdf_file))

    assert parser.extract_text() == ""


# ============================================================
# extract_pagewise_text
# ============================================================

@patch("backend.app.utils.pdf_parser.pdfplumber.open")
def test_extract_pagewise_text(mock_open, tmp_path):

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy")

    p1 = MagicMock()
    p1.extract_text.return_value = "Page One"

    p2 = MagicMock()
    p2.extract_text.return_value = "Page Two"

    pdf = MagicMock()
    pdf.pages = [p1, p2]

    mock_open.return_value.__enter__.return_value = pdf

    parser = PDFParser(str(pdf_file))

    pages = parser.extract_pagewise_text()

    assert len(pages) == 2

    assert pages[0]["page"] == 1
    assert pages[0]["text"] == "Page One"

    assert pages[1]["page"] == 2
    assert pages[1]["text"] == "Page Two"


# ============================================================
# extract_tables
# ============================================================

@patch("backend.app.utils.pdf_parser.pdfplumber.open")
def test_extract_tables(mock_open, tmp_path):

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy")

    page = MagicMock()
    page.extract_tables.return_value = [["A", "B"]]

    pdf = MagicMock()
    pdf.pages = [page]

    mock_open.return_value.__enter__.return_value = pdf

    parser = PDFParser(str(pdf_file))

    tables = parser.extract_tables()

    assert len(tables) == 1
    assert tables[0]["page"] == 1
    assert tables[0]["tables"] == [["A", "B"]]


# ============================================================
# Metadata
# ============================================================

@patch("backend.app.utils.pdf_parser.pdfplumber.open")
def test_get_metadata(mock_open, tmp_path):

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy")

    pdf = MagicMock()
    pdf.pages = [1, 2, 3]
    pdf.metadata = {"Author": "OpenAI"}

    mock_open.return_value.__enter__.return_value = pdf

    parser = PDFParser(str(pdf_file))

    metadata = parser.get_metadata()

    assert metadata["file_name"] == "sample.pdf"
    assert metadata["total_pages"] == 3
    assert metadata["metadata"]["Author"] == "OpenAI"