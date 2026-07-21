import os
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from backend.app.utils.vision_extractor import PDFVisionExtractor


def create_image(size=(300, 300)):
    """
    Create an in-memory PNG image.
    """
    img = Image.new("RGB", size)

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return buffer.getvalue()


# ---------- Quality Tests ----------

def test_high_quality_image():

    extractor = PDFVisionExtractor(min_size_bytes=100)

    img = create_image()

    assert extractor.is_high_quality(img, 300, 300)


def test_small_resolution():

    extractor = PDFVisionExtractor()

    img = create_image((100, 100))

    assert extractor.is_high_quality(img, 100, 100) is False


def test_small_file_size():

    extractor = PDFVisionExtractor(min_size_bytes=10000)

    img = b"123"

    assert extractor.is_high_quality(img, 300, 300) is False


# ---------- Image Extraction ----------

@patch("backend.app.utils.vision_extractor.fitz.open")
def test_extract_images(mock_open, tmp_path):

    extractor = PDFVisionExtractor(
        output_dir=str(tmp_path),
        min_size_bytes=100
    )

    fake_doc = MagicMock()

    fake_doc.__len__.return_value = 1

    fake_page = MagicMock()
    fake_page.get_images.return_value = [(1,)]

    fake_doc.__getitem__.return_value = fake_page

    image_bytes = create_image()

    fake_doc.extract_image.return_value = {
        "image": image_bytes,
        "ext": "png"
    }

    mock_open.return_value = fake_doc

    paths = extractor.extract_images_from_pdf("sample.pdf")

    assert len(paths) == 1
    assert os.path.exists(paths[0])


@patch("backend.app.utils.vision_extractor.fitz.open")
def test_extract_handles_exception(mock_open):

    mock_open.side_effect = Exception("PDF Error")

    extractor = PDFVisionExtractor()

    result = extractor.extract_images_from_pdf("sample.pdf")

    assert result == []