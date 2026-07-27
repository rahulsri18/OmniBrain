from unittest.mock import MagicMock

from app.ingestion.vision_pipeline import VisionIngestionPipeline


def test_ingest_extracted_images_adds_page_metadata():
    pipeline = object.__new__(VisionIngestionPipeline)
    pipeline.db = MagicMock()
    pipeline.collection_name = "omnibrain_vision"
    pipeline.generate_image_embedding = MagicMock(return_value=[0.1] * 512)
    pipeline._extract_page_number = VisionIngestionPipeline._extract_page_number.__get__(
        pipeline,
        VisionIngestionPipeline,
    )

    pipeline.ingest_extracted_images(
        image_paths=["/tmp/report_p7_img1.png"],
        original_pdf_name="report.pdf",
    )

    kwargs = pipeline.db.insert_vectors.call_args.kwargs
    metadata = kwargs["metadata"]

    assert metadata[0]["file_name"] == "report.pdf"
    assert metadata[0]["page"] == 7
    assert metadata[0]["page_number"] == 7
    assert metadata[0]["type"] == "chart_or_image"
    assert metadata[0]["asset_path"].endswith("report_p7_img1.png")
