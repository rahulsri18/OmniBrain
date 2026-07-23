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

import os
from pathlib import Path
from ..utils.pdf_parser import PDFParser  # 🚀 पाथ को प्रोजेक्ट के हिसाब से सही किया
from .chunker import TextChunker
from .embedding import EmbeddingGenerator
from ..vectordb.qdrant_client import QdrantDB

# 🚀 M4 विज़न मॉड्यूल इम्पोर्ट्स
from ..utils.vision_extractor import PDFVisionExtractor
from .vision_pipeline import VisionIngestionPipeline


class IngestionPipeline:
    def __init__(self):
        # M2 और M5 का फिक्स्ड चंकर लॉजिक (अब पैरामीटर्स .env से रीड हो रहे हैं)
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
        self.db = QdrantDB()  # यह अपने आप .env से 384 साइज़ उठा लेगा

        # 🚀 M4 विज़न पाइपलाइन कंपोनेंट्स को इनिशियलाइज़ किया
        self.vision_extractor = PDFVisionExtractor()
        self.vision_pipeline = VisionIngestionPipeline()

    def ingest_pdf(self, pdf_path: str):
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} not found.")

        print("=" * 60)
        print("Starting PDF Ingestion Pipeline")
        print("=" * 60)

        # =========================================================
        # 📝 भाग 1: टेक्स्ट इनजेशन फ्लो (Text Ingestion Flow)
        # =========================================================
        print("\n--- Processing Text Content ---")
        parser = PDFParser(str(pdf_path))
        text = parser.extract_text()

        if not text or not text.strip():
            print("No text found in PDF. Skipping text embedding phase.")
        else:
            # टेक्स्ट को चंक्स में बदलो
            chunks = self.chunker.split_text(text)
            print(f"Generated {len(chunks)} text chunks.")

            # एम्बेडिंग्स जनरेट करो (SentenceTransformers - 384 dim)
            embeddings = self.embedder.generate_embeddings(chunks)
            print(f"Generated {len(embeddings)} text embeddings.")

            # मेटाडेटा तैयार करो
            metadata = [
                {
                    "file_name": pdf_path.name,
                    "chunk": i + 1,
                    "text": chunk,
                    "type": "text"
                }
                for i, chunk in enumerate(chunks)
            ]

            # Qdrant के टेक्स्ट कलेक्शन में सेव करो
            print("Saving text vectors into Qdrant...")
            self.db.insert_vectors(
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata,
            )
            print("Text content successfully stored.")

        # =========================================================
        # 🚀 भाग 2: विज़न इनजेशन फ्लो (M4 Vision Ingestion Flow)
        # =========================================================
        print("\n--- Processing Visual Content (Images/Charts) ---")
        
        # 1. PDF से इमेज निकालो और लो-क्वालिटी फ़िल्टर करो (Day 2 & Day 5)
        extracted_images = self.vision_extractor.extract_images_from_pdf(str(pdf_path))
        print(f"Extracted {len(extracted_images)} high-quality charts/images.")

        # 2. अगर इमेजेस मिली हैं, तो CLIP वेक्टर्स बनाकर स्टोर करो (Day 3 & Day 4)
        if extracted_images:
            print("Processing image features via CLIP and saving to Qdrant...")
            self.vision_pipeline.ingest_extracted_images(
                image_paths=extracted_images,
                original_pdf_name=pdf_path.name
            )
        else:
            print("No high-quality images found to process.")

        print("\n" + "=" * 60)
        print("[Full Multi-Modal Ingestion Completed Successfully!]")
        print("=" * 60)