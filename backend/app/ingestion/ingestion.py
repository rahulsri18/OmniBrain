"""
ingestion.py

End-to-end PDF ingestion pipeline.

Workflow:
PDF
 ↓
Extract Text
 ↓
Chunk Text
 ↓
Generate Embeddings
 ↓
Store in Qdrant
"""

from email import parser
from pathlib import Path

from utils.pdf_parser import PDFParser
from ingestion.chunker import TextChunker
from ingestion.embedding import EmbeddingGenerator
from vectordb.qdrant_client import QdrantDB


class IngestionPipeline:

    def __init__(self):

        

        self.chunker = TextChunker(
            chunk_size=1000,
            chunk_overlap=200,
        )

        self.embedder = EmbeddingGenerator()

        self.db = QdrantDB()

    def ingest_pdf(self, pdf_path: str):

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} not found.")

        parser = PDFParser(str(pdf_path))

        text = parser.extract_text()
        print("=" * 60)
        print("Starting PDF Ingestion Pipeline")
        print("=" * 60)

        print("\nLoading PDF...")

        print("Extracting text...")

        if not text.strip():
            print("No text found.")
            return

        print("Text extraction complete.")

        print("\nChunking text...")

        chunks = self.chunker.split_text(text)

        print(f"Generated {len(chunks)} chunks.")

        print("\nGenerating embeddings...")

        embeddings = self.embedder.generate_embeddings(chunks)

        print(f"Generated {len(embeddings)} embeddings.")

        print("\nPreparing metadata...")

        metadata = []

        for i, chunk in enumerate(chunks):

            metadata.append(
                {
                    "file_name": pdf_path.name,
                    "chunk": i + 1,
                    "text": chunk,
                }
            )

        print("Saving vectors into Qdrant...")

        self.db.insert_vectors(
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata,
        )

        print("\nIngestion Completed Successfully!")

        print("=" * 60)