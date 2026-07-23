import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.app.ingestion.ingestion import IngestionPipeline
from backend.app.vectordb.qdrant_client import QdrantDB


@pytest.mark.integration
@patch("backend.app.ingestion.ingestion.EmbeddingGenerator")
@patch("backend.app.ingestion.ingestion.VisionIngestionPipeline")
@patch("backend.app.ingestion.ingestion.PDFVisionExtractor")
def test_end_to_end_pdf_ingestion(
    mock_pdf_vision,
    mock_vision_pipeline,
    mock_embedding,
):
    """
    End-to-End Integration Test

    Tests:
        PDF -> Parser -> Chunker -> Fake Embeddings
        -> Real Qdrant -> Verify Storage
    """

    # ---------------------------------------------------
    # Sample PDF
    # ---------------------------------------------------

    sample_pdf = Path("tests/data/sample.pdf")

    assert sample_pdf.exists(), (
        "Place sample.pdf inside tests/data/"
    )

    # ---------------------------------------------------
    # Mock Embedding Generator
    # ---------------------------------------------------

    fake_embedder = MagicMock()

    def fake_generate_embeddings(chunks):
        """
        Return one fake 384-dimensional embedding
        for every generated text chunk.
        """
        return [
            [0.01] * 384
            for _ in chunks
        ]

    fake_embedder.generate_embeddings.side_effect = fake_generate_embeddings

    mock_embedding.return_value = fake_embedder

    # ---------------------------------------------------
    # Mock Vision Extractor
    # ---------------------------------------------------

    fake_extractor = MagicMock()

    fake_extractor.extract_images_from_pdf.return_value = []

    mock_pdf_vision.return_value = fake_extractor

    # ---------------------------------------------------
    # Mock Vision Pipeline
    # ---------------------------------------------------

    mock_vision_pipeline.return_value = MagicMock()

    # ---------------------------------------------------
    # Temporary Qdrant Collection
    # ---------------------------------------------------

    collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"

    db = QdrantDB(
        collection_name=collection_name,
        vector_size=384,
    )

    try:

        print("\n" + "=" * 60)
        print("STARTING END-TO-END PDF INGESTION TEST")
        print("=" * 60)

        pipeline = IngestionPipeline()

        print("✓ IngestionPipeline initialized")

        pipeline.db = db

        print("✓ Connected to temporary Qdrant collection")

        pipeline.ingest_pdf(str(sample_pdf))

        print("✓ PDF ingestion completed")

        # ---------------------------------------------------
        # Verify Collection Exists
        # ---------------------------------------------------

        collections = db.client.get_collections().collections

        collection_names = [
            collection.name
            for collection in collections
        ]

        assert (
            collection_name in collection_names
        ), "Qdrant collection was not created."

        print("✓ Collection created successfully")

        # ---------------------------------------------------
        # Verify Stored Vectors
        # ---------------------------------------------------

        info = db.client.get_collection(collection_name)

        assert (
            info.points_count > 0
        ), "No vectors were stored in Qdrant."

        print(f"✓ Stored vectors : {info.points_count}")

        print("=" * 60)
        print("END-TO-END TEST PASSED")
        print("=" * 60)

    finally:

        try:

            db.client.delete_collection(collection_name)

            print("✓ Temporary Qdrant collection deleted")

        except Exception as e:

            print(f"Cleanup skipped: {e}")