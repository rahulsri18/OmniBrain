"""
ingestion.py

End-to-end Multi-Modal PDF ingestion pipeline.

Workflow:
PDF
 ↓
├── Extract Text → Chunk Text → Generate Text Embeddings → Store in Qdrant (384-dim)
↓
└── Extract Images → Filter Low-Quality → Generate CLIP Embeddings → Store in Qdrant (512-dim)
"""

from pathlib import Path
from ..utils.pdf_parser import PDFParser

from ..utils.vision_extractor import PDFVisionExtractor
from ..vectordb.qdrant_client import QdrantDB
from .chunker import TextChunker
from .embedding import EmbeddingGenerator
from .vision_pipeline import VisionIngestionPipeline


class IngestionPipeline:
    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
        self.db = QdrantDB()

        self.vision_extractor = PDFVisionExtractor()
        self.vision_pipeline = VisionIngestionPipeline()

    def ingest_pdf(self, pdf_path: str):
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} not found.")
        if pdf_path.stat().st_size == 0:
            raise ValueError("Uploaded PDF is empty.")

        print("=" * 60)
        print("Starting PDF Ingestion Pipeline")
        print("=" * 60)

        # =========================================================
        # =========================================================
        print("\n--- Processing Text Content ---")
        try:
            parser = PDFParser(str(pdf_path))
        except Exception as e:
            raise ValueError(f"Unable to open PDF. The file may be corrupted or invalid. ({e})")
        
        chunks = []
        metadata = []

        pagewise_text = None
        try:
            pagewise_text = parser.extract_pagewise_text()
        except Exception:
            pagewise_text = None

        if isinstance(pagewise_text, list) and pagewise_text:
            chunk_index = 0

            for page_entry in pagewise_text:
                if not isinstance(page_entry, dict):
                    continue

                page_number = page_entry.get("page")
                page_text = page_entry.get("text", "")

                if not page_text or not page_text.strip():
                    continue

                page_chunks = self.chunker.split_text(page_text)

                for chunk in page_chunks:
                    chunk_index += 1
                    chunks.append(chunk)

                    page_metadata = {
                        "file_name": pdf_path.name,
                        "chunk": chunk_index,
                        "text": chunk,
                        "type": "text",
                    }

                    if page_number is not None:
                        page_metadata["page"] = page_number
                        page_metadata["page_number"] = page_number

                    metadata.append(page_metadata)

        if not chunks:
            text = parser.extract_text()

            if not text or not text.strip():
                    raise ValueError("No readable text found in the uploaded PDF.")
            else:
                chunks = self.chunker.split_text(text)
                print(f"Generated {len(chunks)} text chunks.")

                metadata = [
                    {
                        "file_name": pdf_path.name,
                        "chunk": i + 1,
                        "text": chunk,
                        "type": "text",
                    }
                    for i, chunk in enumerate(chunks)
                ]

        if chunks:
            print(f"Generated {len(chunks)} text chunks.")

            embeddings = self.embedder.generate_embeddings(chunks)
            print(f"Generated {len(embeddings)} text embeddings.")

            print("Saving text vectors into Qdrant...")
            self.db.insert_vectors(
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata,
            )
            print("Text content successfully stored.")

        # =========================================================
        # =========================================================
        print("\n--- Processing Visual Content (Images/Charts) ---")

        try:
            extracted_images = self.vision_extractor.extract_images_from_pdf(str(pdf_path))
        except Exception as e:
            print(f"Image extraction failed: {e}")
            extracted_images = []
        print(f"Extracted {len(extracted_images)} high-quality charts/images.")

        if extracted_images:
            print("Processing image features via CLIP and saving to Qdrant...")
            self.vision_pipeline.ingest_extracted_images(
                image_paths=extracted_images, original_pdf_name=pdf_path.name
            )
        else:
            print("No high-quality images found to process.")

        print("\n" + "=" * 60)
        print("[Full Multi-Modal Ingestion Completed Successfully!]")
        print("=" * 60)
