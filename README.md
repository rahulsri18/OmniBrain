# OmniBrain 🧠
> High-Performance, Enterprise-Ready Retrieval-Augmented Generation (RAG) Platform

OmniBrain is an end-to-end RAG application designed for fast, accurate document ingestion and context-aware querying. Built with a **FastAPI** backend, **Streamlit** frontend, **Qdrant** vector database, and **Redis** caching layer, OmniBrain processes unstructured PDFs, generates high-dimensional embeddings, and streams accurate, grounded responses with low latency.

---

## 🛠️ Tech Stack & Key Components

- **Frontend Container:** Streamlit
- **Backend API Container:** FastAPI, Uvicorn Engine
- **Data Ingestion & Parsing:** `pdfplumber`, `pdfminer.six`, `langchain-text-splitters`
- **Vector Database Container:** Qdrant Vector DB
- **Caching Container:** Redis Engine
- **Embedding Models:** Sentence Transformers (`all-MiniLM-L6-v2`) / OpenAI Embeddings

---

## 🏗️ Technical Architecture

+---------------------------------------------------------------------------------+
|                                 USER INTERFACE                                  |
|                         Streamlit Frontend (Port 8501)                          |
+---------------------------------------------------------------------------------+
|
| HTTP / Async REST API
v
+---------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                  |
|                            (Uvicorn Engine - Port 8000)                         |
+---------------------------------------------------------------------------------+
|                                       |                          |
| Document Payload                      | Session / Query Cache    | Vector Context
v                                       v                          v
+-----------------------+               +-------------------+      +-------------------+
|  INGESTION PIPELINE   |               |   REDIS ENGINE    |      |  QDRANT VECTOR DB |
|  - PDFParser          |               |    (Port 6379)    |      | (Port 6333/6334)  |
|  - Text Splitters     |               |  - Session State  |      | - Vector Indexing |
|  - SentenceTransformer|               |  - Sub-second     |      | - Cosine Distance |
+-----------------------+               |    Query Cache    |      |   Similarity Search|
+-------------------+      +-------------------+

### Component Overview
1. **Frontend (Streamlit):** Web UI providing drag-and-drop file upload, session monitoring, and streaming chat outputs.
2. **Backend API (FastAPI):** Asynchronous backend exposing endpoints (`/api/v1/ingest`, `/api/v1/chat`) to manage data pipelines.
3. **Ingestion Pipeline:** Uses `PDFParser` and `langchain-text-splitters` to extract and split document text into semantic overlapping chunks.
4. **Vector Database (Qdrant):** Stores 384-dimensional dense vectors with metadata payloads for high-speed similarity retrieval.
5. **Caching Layer (Redis):** Caches frequent user query signatures and active session states to optimize latency and cut API costs.

---

## 🐳 Setup & Deployment Guide (Docker)

### Prerequisites
- **Docker Desktop** installed on your system (Windows, macOS, or Linux).
- **Docker Compose** enabled (`v2.0+` recommended).

---

### Step 1: Clone the Repository

```bash
git clone [https://github.com/rahulsri18/OmniBrain.git](https://github.com/rahulsri18/OmniBrain.git)
cd OmniBrain

Create a .env file in the root directory of the project:
# Application Host & Ports
BACKEND_PORT=8000
FRONTEND_PORT=8501

# Docker Internal Service Hosts
QDRANT_HOST=qdrant
QDRANT_PORT=6333

REDIS_HOST=redis
REDIS_PORT=6379

# API Keys
OPENAI_API_KEY=your_openai_api_key_here

Step 3: Build and Launch All Microservices
Run the following command to build the Docker images and start all 4 services (Backend, Frontend, Qdrant, Redis) in detached mode:


docker compose up -d --build
Step 4: Verify Running Containers
Check the status of your microservices:

docker compose ps
You should see 4 active containers:

omnibrain-backend (FastAPI)

omnibrain-frontend (Streamlit)

omnibrain-qdrant (Qdrant DB)

omnibrain-redis (Redis Cache)

Docker Useful Commands
View live logs across all containers:

docker compose logs -f
View logs for backend service only:

docker compose logs -f backend
Stop all running services:

docker compose down
Stop services and clear persistent volume data:

docker compose down -v