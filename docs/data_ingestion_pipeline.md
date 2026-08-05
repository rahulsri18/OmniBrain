Data Ingestion Pipeline
OmniBrain – M2 (Data / Ingestion Engineer)
-------------------------------------------------------------------------------------------------------------------
1. Overview

The Data Ingestion Pipeline is responsible for converting uploaded PDF documents into searchable vector representations that can be efficiently retrieved by the Retrieval-Augmented Generation (RAG) system.

The pipeline extracts document content, splits it into meaningful chunks, generates semantic embeddings in batches, stores them in the Qdrant vector database, and supports a hybrid (text + image) retrieval layer with several quality-control stages layered on top: relevance grading, query rewriting, factual grounding verification, and a Redis cache for repeated queries.

2. Architecture Diagram
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