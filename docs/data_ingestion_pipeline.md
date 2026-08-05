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

3.5 Embedding Generation:

Model: sentence-transformers/all-MiniLM-L6-v2 Output: 384-dimensional, normalized embedding vectors

Chunks are embedded in batches rather than one at a time.

Traditional (one-at-a-time) approach:

text
Chunk 1 → Model
Chunk 2 → Model
Chunk 3 → Model
...

For a document with 1000 chunks, this means 1000 separate model invocations.

Batched approach:

text
32 Chunks
    │
    ▼
Embedding Model
    │
    ▼
32 Embeddings

1000 chunks at a batch size of 32 becomes roughly 32 model invocations instead of 1000, producing the same embeddings with substantially less overhead.

Features:

Normalized embeddings (improves cosine similarity search)
Configurable batch size (constructor default, overridable per call)
Empty/whitespace chunks are skipped before encoding, with output-list length always matching input-list length so downstream code can zip embeddings back to their original chunks safely
3.6 Metadata Generation

Each chunk is stored alongside metadata describing where it came from:

json
{
    "file_name": "sample.pdf",
    "page": 5,
    "chunk_index": 12
}

Metadata enables scoped retrieval (e.g. searching within a specific page or page range).

3.7 Vector Storage (Qdrant):

Database: Qdrant
Collection: omnibrain (text), omnibrain_vision (images)
Stored per point: embedding vector, chunk text, metadata payload