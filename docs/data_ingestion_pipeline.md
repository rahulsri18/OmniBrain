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

3.7 Vector Storage (Qdrant):

Database: Qdrant
Collection: omnibrain (text), omnibrain_vision (images)
Stored per point: embedding vector, chunk text, metadata payload

3.8 Hybrid Search Retrieval:

At query time, the retriever generates a query embedding, searches Qdrant for both semantic text matches and CLIP-based text→image matches, deduplicates results, filters out low-relevance matches, and merges everything into a single ranked response.

3.9 Redis Cache Layer:

Before repeating the embed-and-search work, search_text() checks a Redis cache keyed by the normalized query plus its search parameters (top_k, page filters, etc.). On a cache hit, neither embedding generation nor the Qdrant call runs — the cached result is returned directly. On a miss, the search proceeds as normal and the result is cached for next time. The cache fails safe: if Redis is unreachable, retrieval falls through to Qdrant exactly as if no cache existed.

3.10 Document Grader:

An LLM-based relevance grader evaluates each retrieved chunk against the user's question, classifying it as relevant or not before it's passed to generation — reducing noise from chunks that only share surface keywords with the query.

3.11 Query Transformer:

If document grading determines that too few retrieved chunks are relevant, a query-rewriting helper reformulates the original query into clearer search-oriented terms (expanding abbreviations, resolving vague pronouns, stripping conversational filler) and retrieval is retried with the rewritten query — without ever answering the question itself.

3.12 Factual Grounding Verification:

After the LLM generates an answer, a grounding verifier checks each factual claim in that answer against the retrieved context, classifying claims as supported, unsupported, or contradicted. Answers with no context, or with grounding below a configurable threshold, are flagged rather than returned as-is — reducing hallucinated or unsupported claims in the final response.