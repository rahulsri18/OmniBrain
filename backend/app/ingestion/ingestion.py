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


from pathlib import Path
from utils.pdf_parser import PDFParser  # 🚀 पाथ को प्रोजेक्ट के हिसाब से सही किया
from app.ingestion.chunker import TextChunker
from app.ingestion.embedding import EmbeddingGenerator
from app.vectordb.qdrant_client import QdrantDB


class IngestionPipeline:
    def _init_(self):
        self.chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        self.embedder = EmbeddingGenerator()
        self.db = QdrantDB()  # यह अपने आप .env से 384 साइज़ उठा लेगा

    def ingest_pdf(self, pdf_path: str):
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} not found.")

        # PDF से टेक्स्ट निकालो
        parser = PDFParser(str(pdf_path))
        text = parser.extract_text()
        
        print("=" * 60)
        print("Starting PDF Ingestion Pipeline")
        print("=" * 60)

        if not text.strip():
            print("No text found in PDF.")
            return

        # टेक्स्ट को चंक्स में बदलो
        chunks = self.chunker.split_text(text)
        print(f"Generated {len(chunks)} chunks.")

        # एम्बेडिंग्स जनरेट करो (SentenceTransformers)
        embeddings = self.embedder.generate_embeddings(chunks)
        print(f"Generated {len(embeddings)} embeddings.")

        # मेटाडेटा तैयार करो
        metadata = [
            {
                "file_name": pdf_path.name,
                "chunk": i + 1,
                "text": chunk
            }
            for i, chunk in enumerate(chunks)
        ]

        # Qdrant में सेव करो
        print("Saving vectors into Qdrant...")
        self.db.insert_vectors(
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata,
        )

        print("\nIngestion Completed Successfully!")
        print("=" * 60)