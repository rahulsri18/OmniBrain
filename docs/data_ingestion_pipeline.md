Data Ingestion Pipeline
OmniBrain – M2 (Data / Ingestion Engineer)
-------------------------------------------------------------------------------------------------------------------
1. Overview
------------

The Data Ingestion Pipeline is responsible for converting uploaded PDF documents into searchable vector representations that can be efficiently retrieved by the Retrieval-Augmented Generation (RAG) system.

The pipeline extracts document content, splits it into meaningful chunks, generates semantic embeddings in batches, stores them in the Qdrant vector database, and supports a hybrid (text + image) retrieval layer with several quality-control stages layered on top: relevance grading, query rewriting, factual grounding verification, and a Redis cache for repeated queries.

2. Architecture Diagram
-----------------------
                PDF Upload
                     │
                     ▼
                PDF Parser
                     │
                     ▼
             Text Extraction
                     │
                     ▼
             Text Chunking
                     │
                     ▼
        Batch Embedding Generation
                     │
                     ▼
          Metadata Generation
                     │
                     ▼
             Qdrant Vector DB
                     │
                     ▼
          Hybrid Search Retrieval
                     │
                     ▼
             Redis Cache Layer
                     │
                     ▼
             Document Grader
                     │
                     ▼
            Generator (LLM)
                     │
                     ▼
         Factual Grounding Verifier
-------------------------------------------------------------------------------

3. Pipeline Flow
-----------------

3.1 PDF Upload:

A user uploads a PDF document to be ingested and made searchable.

3.2 PDF Parsing:

Responsibility: Extract raw textual content from the uploaded PDF.

Input: PDF document
Output: Raw document text (per page)
Purpose: Prepares the document for downstream chunking and embedding.

3.3 Text Extraction:

Text is pulled out of the parsed PDF structure, preserving page boundaries so later stages (metadata, page-scoped retrieval) can reference where each piece of text came from.

3.4 Text Chunking:

Responsibility: Split extracted text into smaller, semantically coherent chunks sized to fit the embedding model's input limits.

Parameter	Value
Chunk Size	1000 characters
Chunk Overlap	200 characters

Benefits:

Preserves context across chunk boundaries
Improves retrieval accuracy
Fits embedding model input limits