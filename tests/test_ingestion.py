from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.ingestion import IngestionPipeline

#TEST CASE 1: Missing PDF File

@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_missing_pdf(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
):
    pipeline = IngestionPipeline()

    with pytest.raises(FileNotFoundError):
        pipeline.ingest_pdf("missing.pdf")

from unittest.mock import MagicMock

# ============================================================
# TEST CASE 2: PDF has no readable text
# ============================================================

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_empty_text_pdf(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    # Create a dummy PDF file
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    # Mock PDFParser
    parser_instance = MagicMock()

    # No readable text
    parser_instance.extract_pagewise_text.return_value = []
    parser_instance.extract_text.return_value = ""

    mock_parser.return_value = parser_instance

    pipeline = IngestionPipeline()

    # Current application behavior:
    # PDF with no readable text is rejected.
    with pytest.raises(
        ValueError,
        match="No readable text found in the uploaded PDF",
    ):
        pipeline.ingest_pdf(str(pdf))

    # Verify text processing did not continue
    pipeline.chunker.split_text.assert_not_called()
    pipeline.embedder.generate_embeddings.assert_not_called()
    pipeline.db.insert_vectors.assert_not_called()

#TEST CASE 3: Successful Text Ingestion

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_successful_text_ingestion(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "This is a sample document."
    mock_parser.return_value = parser

    mock_chunker.return_value.split_text.return_value = [
        "Chunk 1",
        "Chunk 2",
    ]

    mock_embedder.return_value.generate_embeddings.return_value = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()
    pipeline.ingest_pdf(str(pdf))

    pipeline.chunker.split_text.assert_called_once_with(
        "This is a sample document."
    )

    pipeline.embedder.generate_embeddings.assert_called_once_with(
        ["Chunk 1", "Chunk 2"]
    )

    pipeline.db.insert_vectors.assert_called_once()

    kwargs = pipeline.db.insert_vectors.call_args.kwargs

    assert kwargs["chunks"] == ["Chunk 1", "Chunk 2"]
    assert len(kwargs["embeddings"]) == 2
    assert len(kwargs["metadata"]) == 2

# ============================================================
# TEST CASE 4: Metadata Validation
# ============================================================

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_metadata_generation(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()

    # Provide actual page-wise information.
    parser.extract_pagewise_text.return_value = [
        {
            "page": 1,
            "text": "Metadata Test Page One",
        },
        {
            "page": 2,
            "text": "Metadata Test Page Two",
        },
    ]

    parser.extract_text.return_value = ""

    mock_parser.return_value = parser

    # One chunk per page
    mock_chunker.return_value.split_text.side_effect = [
        ["Chunk A"],
        ["Chunk B"],
    ]

    mock_embedder.return_value.generate_embeddings.return_value = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()

    pipeline.ingest_pdf(str(pdf))

    kwargs = pipeline.db.insert_vectors.call_args.kwargs

    metadata = kwargs["metadata"]

    # Two chunks should be generated
    assert len(metadata) == 2

    # --------------------------------------------------------
    # Page 1 metadata
    # --------------------------------------------------------

    assert metadata[0]["file_name"] == "sample.pdf"
    assert metadata[0]["chunk"] == 1
    assert metadata[0]["type"] == "text"
    assert metadata[0]["text"] == "Chunk A"
    assert metadata[0]["page"] == 1
    assert metadata[0]["page_number"] == 1

    # --------------------------------------------------------
    # Page 2 metadata
    # --------------------------------------------------------

    assert metadata[1]["file_name"] == "sample.pdf"
    assert metadata[1]["chunk"] == 2
    assert metadata[1]["type"] == "text"
    assert metadata[1]["text"] == "Chunk B"
    assert metadata[1]["page"] == 2
    assert metadata[1]["page_number"] == 2

#TEST CASE 5: Multiple Chunks Handling
@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_multiple_chunks_processing(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "Large document"
    mock_parser.return_value = parser

    chunks = [
        "Chunk 1",
        "Chunk 2",
        "Chunk 3",
        "Chunk 4",
    ]

    embeddings = [
        [0.1] * 384,
        [0.2] * 384,
        [0.3] * 384,
        [0.4] * 384,
    ]

    mock_chunker.return_value.split_text.return_value = chunks
    mock_embedder.return_value.generate_embeddings.return_value = embeddings
    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()
    pipeline.ingest_pdf(str(pdf))

    pipeline.chunker.split_text.assert_called_once_with("Large document")

    pipeline.embedder.generate_embeddings.assert_called_once_with(chunks)

    pipeline.db.insert_vectors.assert_called_once()

    kwargs = pipeline.db.insert_vectors.call_args.kwargs

    assert kwargs["chunks"] == chunks
    assert kwargs["embeddings"] == embeddings

    metadata = kwargs["metadata"]

    assert len(metadata) == 4

    for i in range(4):
        assert metadata[i]["file_name"] == "sample.pdf"
        assert metadata[i]["chunk"] == i + 1
        assert metadata[i]["type"] == "text"
        assert metadata[i]["text"] == chunks[i]

#TEST CASE 6: No Images Extracted

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_no_images_found(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "Sample text"
    mock_parser.return_value = parser

    mock_chunker.return_value.split_text.return_value = ["Chunk 1"]

    mock_embedder.return_value.generate_embeddings.return_value = [
        [0.1] * 384
    ]

    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()

    pipeline.ingest_pdf(str(pdf))

    pipeline.db.insert_vectors.assert_called_once()

    pipeline.vision_pipeline.ingest_extracted_images.assert_not_called()

#TEST CASE 7: Images Processed Successfully

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_images_processed_successfully(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "This is sample text."
    mock_parser.return_value = parser

    mock_chunker.return_value.split_text.return_value = [
        "Chunk 1"
    ]

    mock_embedder.return_value.generate_embeddings.return_value = [
        [0.1] * 384
    ]

    image_paths = [
        "image1.png",
        "image2.png",
        "image3.png",
    ]

    mock_extractor.return_value.extract_images_from_pdf.return_value = image_paths

    pipeline = IngestionPipeline()

    pipeline.ingest_pdf(str(pdf))

    pipeline.db.insert_vectors.assert_called_once()

    pipeline.vision_pipeline.ingest_extracted_images.assert_called_once_with(
        image_paths=image_paths,
        original_pdf_name="sample.pdf",
    )

#TEST CASE 8: PDF Parser Exception

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_pdf_parser_exception(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.side_effect = RuntimeError("Failed to parse PDF")
    mock_parser.return_value = parser

    pipeline = IngestionPipeline()

    with pytest.raises(RuntimeError, match="Failed to parse PDF"):
        pipeline.ingest_pdf(str(pdf))

    pipeline.chunker.split_text.assert_not_called()
    pipeline.embedder.generate_embeddings.assert_not_called()
    pipeline.db.insert_vectors.assert_not_called()
    pipeline.vision_pipeline.ingest_extracted_images.assert_not_called()

#TEST CASE 9: Embedding Generation Exception

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_embedding_generation_exception(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "This is sample text."
    mock_parser.return_value = parser

    mock_chunker.return_value.split_text.return_value = [
        "Chunk 1",
        "Chunk 2",
    ]

    mock_embedder.return_value.generate_embeddings.side_effect = RuntimeError(
        "Embedding model failed"
    )

    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()

    with pytest.raises(RuntimeError, match="Embedding model failed"):
        pipeline.ingest_pdf(str(pdf))

    pipeline.chunker.split_text.assert_called_once()

    pipeline.embedder.generate_embeddings.assert_called_once()

    pipeline.db.insert_vectors.assert_not_called()

    pipeline.vision_pipeline.ingest_extracted_images.assert_not_called()

#TEST CASE 10: Database Insertion Exception

@patch("app.ingestion.ingestion.PDFParser")
@patch("app.ingestion.ingestion.VisionIngestionPipeline")
@patch("app.ingestion.ingestion.PDFVisionExtractor")
@patch("app.ingestion.ingestion.QdrantDB")
@patch("app.ingestion.ingestion.EmbeddingGenerator")
@patch("app.ingestion.ingestion.TextChunker")
def test_database_insertion_exception(
    mock_chunker,
    mock_embedder,
    mock_db,
    mock_extractor,
    mock_vision,
    mock_parser,
    tmp_path,
):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")

    parser = MagicMock()
    parser.extract_text.return_value = "Database failure test"
    mock_parser.return_value = parser

    chunks = ["Chunk 1", "Chunk 2"]

    embeddings = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    mock_chunker.return_value.split_text.return_value = chunks
    mock_embedder.return_value.generate_embeddings.return_value = embeddings

    mock_db.return_value.insert_vectors.side_effect = ConnectionError(
        "Qdrant connection failed"
    )

    mock_extractor.return_value.extract_images_from_pdf.return_value = []

    pipeline = IngestionPipeline()

    with pytest.raises(ConnectionError, match="Qdrant connection failed"):
        pipeline.ingest_pdf(str(pdf))

    pipeline.chunker.split_text.assert_called_once_with(
        "Database failure test"
    )

    pipeline.embedder.generate_embeddings.assert_called_once_with(
        chunks
    )

    pipeline.db.insert_vectors.assert_called_once()

    pipeline.vision_pipeline.ingest_extracted_images.assert_not_called()