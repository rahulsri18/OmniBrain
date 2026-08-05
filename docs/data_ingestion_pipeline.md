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


4. Components:

File	Responsibility
parser.py	Extracts raw text from uploaded PDFs.
chunker.py	Splits extracted text into overlapping, sized chunks.
embedding.py	Generates normalized embeddings, single-text and batched, via all-MiniLM-L6-v2.
vector_store.py / qdrant_client.py	Manages the Qdrant client: collection creation, vector insertion, similarity search.
hybrid_search.py	Combines semantic text search and CLIP-based image search; integrates the Redis cache in front of search_text().
retrieval_filter.py	Filters out low-relevance results using configurable thresholds.
deduplication.py	Detects and removes duplicate retrieved chunks via hashing.
document_grader.py	LLM-powered relevance grading of retrieved chunks (supported/unsupported classification, retry logic, JSON parsing, safe fallbacks).
query_transformer.py	Rewrites queries into better search terms when retrieval quality is insufficient.
factual_grounding.py	Verifies that generated answers are supported by retrieved context; flags unsupported or contradicted claims.
redis_cache.py	Caches retrieval results (get/set/delete/clear) keyed by query + search parameters, with fail-safe fallback if Redis is unavailable.
vision_pipeline.py	Handles image ingestion/embedding for the multimodal (CLIP-based) retrieval path.
ban_list.py	Guardrails configuration: categorized keyword lists (abusive, hate, politics, violence, adult, illegal, prompt injection, spam, out-of-scope) consumed by the safety layer ahead of retrieval.

5. Configuration:

Embedding Configuration
Parameter	Value
Model	all-MiniLM-L6-v2
Vector Size	384
Batch Size	32 (configurable)
Chunking Configuration
Parameter	Value
Chunk Size	1000
Chunk Overlap	200
Qdrant Configuration
Parameter	Default
Host	localhost
Port	6333
Collection	omnibrain (text), omnibrain_vision (images)
Redis Cache Configuration
Parameter	Default
Host	localhost
Port	6379
DB	0
TTL	300 seconds
Key Prefix	retrieval_cache
Grounding / Grading Configuration
Parameter	Default
Grounded score threshold	0.7
Grader relevance threshold	0.5
Max retries (LLM calls)	2

6. Storage Structure:

Each Qdrant point stores:

json
{
    "id": "<point id>",
    "vector": [0.01, -0.02, ...],
    "payload": {
        "text": "<chunk text>",
        "file_name": "sample.pdf",
        "page": 5,
        "chunk_index": 12
    }
}

Redis cache entries store the serialized retrieval result under a key derived from a hash of the normalized query and its search parameters, with a configurable TTL.

7. Error Handling:

The ingestion and retrieval pipeline handles the following scenarios:

Empty PDF files
Empty or whitespace-only text chunks (skipped before embedding, with output alignment preserved)
Embedding generation failures
Qdrant connection failures
Invalid or missing metadata
Batch processing errors
Redis cache unavailable (fails safe — falls through to Qdrant)
LLM API failures in the grader, query transformer, and grounding verifier (retried with backoff, then a configurable fallback policy)
Malformed/unparsable LLM JSON output (treated as a safe default rather than raising)
No retrieved context at generation time (grounding verifier fails closed rather than assuming grounded)

8. Performance Optimizations:

Batch embedding generation — reduces model invocations from one-per-chunk to one-per-batch.
Configurable batch size — tunable based on available CPU/GPU memory.
Normalized embeddings — improves cosine similarity search quality.
Redis caching of retrieval results — repeated identical queries skip embedding generation and the Qdrant call entirely.
Metadata storage — supports efficient page-level and scoped retrieval without full-collection scans.

9. Future Improvements:

Asynchronous ingestion pipeline
Incremental document updates
Parallel PDF processing
Distributed embedding generation
OCR support for scanned PDFs
Automatic duplicate document detection
Caching embeddings and/or LLM outputs (explicitly out of scope for the current retrieval-result cache)

10. Technologies Used:

Python
Sentence Transformers
PyTorch
Qdrant
Redis
Anthropic Claude API
CLIP (openai/clip-vit-base-patch32)

11. Conclusion:

The data ingestion pipeline forms the foundation of the OmniBrain Retrieval-Augmented Generation system. It transforms uploaded PDF documents into searchable semantic vectors while preserving document context and metadata, and pairs that with a hybrid retrieval layer that grades relevance, rewrites poor queries, caches repeated searches, and verifies that generated answers stay grounded in retrieved context. Together these stages improve indexing throughput, retrieval precision, and answer reliability for downstream question-answering tasks.