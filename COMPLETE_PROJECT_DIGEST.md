# LocalLens: Complete Project Source & Architecture Digest

This document consolidates the entire technical context of the **LocalLens** project, including architecture, implementation logic, database schemas, and configuration. It is designed to provide a comprehensive source for AI-driven analysis and presentation generation.

---

## 1. Executive Summary
**LocalLens** is a high-performance, **privacy-first Retrieval-Augmented Generation (RAG)** system for local document intelligence. It enables users to interact with private document collections (PDFs, images, diagrams) using natural language, ensuring 100% data sovereignty by running entirely locally on Linux systems.

### Key Performance Pillars:
- **Offline Sovereignty:** No data egress; local LLM (Llama-3 8B) and local vector/relational DBs.
- **Multimodal Retrieval:** Unified search across text and visual document regions (charts/diagrams).
- **Verifiable RAG:** Integrated hallucination checking and page-level visual citations.
- **Design Excellence:** Premium "Glassmorphism" UI for an immersive research workspace.

---

## 2. Team Work Division & Implementation Roles

### Person A (UI/UX Engineer): Frontend Architecture & Logic
- **Primary Tech:** React 19, Vite, TypeScript, Tailwind CSS, Playwright.
- **Key Contributions:**
  - Implementation of the **Glassmorphism Design System** (blur filters, translucency).
  - Development of the **Document Workspace** and **Chat Interface** with real-time SSE streaming.
  - Integration of **Citation Hotspots** for visual verification.
  - Automated UI verification using **Playwright** E2E tests.

### Person B (Data Ingestion & Storage Reliability): Ingestion Pipeline
- **Primary Tech:** Python, PyPDF2, Tesseract OCR, OpenCV, PostgreSQL.
- **Key Contributions:**
  - **Multimodal Extraction:** High-fidelity text extraction from native and scanned PDFs.
  - **Visual Region Extraction:** Automated detection/cropping of diagrams and charts using OpenCV.
  - **Storage Architecture:** Design and management of the PostgreSQL relational schema.
  - **Background Ingestion:** Implementation of asynchronous threading for non-blocking uploads.

### Person C (Vector Architecture & Hybrid Retrieval): Search & Infrastructure
- **Primary Tech:** Milvus, Sentence-Transformers (SBERT), Open CLIP, BM25, Docker.
- **Key Contributions:**
  - **Hybrid Search Engine:** Combining Dense (Milvus) and Sparse (BM25) search with **Reciprocal Rank Fusion (RRF)**.
  - **Vector Database Ops:** Managing Milvus indices, collections, and multimodal embedding pipelines.
  - **Infrastructure:** Orchestrating the local multi-service stack via **Docker Compose**.
  - **Cross-Modal Search:** Implementing text-to-image retrieval using CLIP.

### Person D (RAG Generation & API Orchestration): Generation & AI
- **Primary Tech:** FastAPI, LangChain, llama-cpp-python, Pydantic.
- **Key Contributions:**
  - **Local LLM Serving:** Optimized inference for 4-bit quantized GGUF models with GPU acceleration.
  - **RAG Orchestration:** Managing LangChain pipelines, dynamic context scoping, and chat history.
  - **Output Verification:** Development of the **Hallucination Checker** and **Citation Mapper**.
  - **API Design:** Architecting the core FastAPI routes (Query, Ingest, Session, Document).

---

## 3. System Architecture & Core Logic

### 3.1 Backend Entry & API Structure (`backend/main.py`)
- **FastAPI Core:** Manages CORS, includes routers for Documents, Sessions, Queries, and Ingestion.
- **Lifecycle Management:** Initializes PostgreSQL and Milvus on startup.
- **Static Asset Serving:** Serves internally cropped images for visual citations.

### 3.2 Configuration & Models (`backend/config.py`)
- **LLM:** Optimized for `Qwen3-8B-Q4_K_M.gguf`.
- **Embeddings:** Text (`all-MiniLM-L6-v2`), Image (`openai/clip-vit-base-patch32`).
- **Tuning:** Chunk size (768), Overlap (128), Retrieval Top-K (10).
- **RAM Guard:** Minimum 3GB free RAM required before loading LLM.

### 3.3 Relational Schema (`backend/storage/schema.sql`)
- **`documents`**: Metadata, filename, page count, and MD5 file hash (for de-duplication).
- **`text_chunks`**: Content, page number, and mapping to Milvus vector IDs.
- **`image_regions`**: Bounding boxes (X1, Y1, X2, Y2), page numbers, and image paths.
- **`chat_sessions` & `chat_messages`**: Full history persistence with citation and verification metadata.
- **`session_documents`**: Dynamic mapping for document-specific context scoping.

### 3.4 Ingestion Service (`backend/api/services/ingestion_service.py`)
- **Workflow:** Extraction -> Semantic Chunking -> Embedding -> Indexing.
- **Visual Detection:** OpenCV identifies diagrams; CLIP embeds them for multimodal search.
- **Relational Sync:** Bulk inserts into PostgreSQL and Milvus ensure atomic updates.

### 3.5 Retrieval Logic (`backend/api/routes/query_routes.py`)
- **Hybrid Retrieval:** Executes Dense (Milvus) and Sparse (BM25) searches in parallel via `asyncio.gather`.
- **RRF Fusion:** Merges text and image results into a single ranked list.
- **Streaming RAG:** Implements SSE (`StreamingResponse`) to deliver answers token-by-token.
- **Post-hoc Processing:** Automatically triggers Hallucination Checking and Citation Mapping after generation.

### 3.6 Generation Pipeline (`backend/generation/`)
- **`llm_runner.py`**: Wraps `llama-cpp-python`; handles lazy-loading, GPU offloading, and streaming with `<think>` block removal.
- **`prompt_builder.py`**: Constructs strict RAG prompts with numbered excerpts and markdown-free formatting.
- **`hallucination_checker.py`**: Uses NLI-based cosine similarity to verify every sentence in the AI's answer against source chunks.

### 3.7 Vector Storage (`backend/storage/milvus_store.py`)
- **Collections:** Separate collections for Text (384-dim) and Image (512-dim) embeddings.
- **Indexing:** Uses HNSW (Hierarchical Navigable Small World) for sub-second retrieval.

---

## 4. Frontend & User Experience

### 4.1 UI Design System
- **Aesthetic:** High-end "Glassmorphism" featuring `backdrop-blur` and neutral translucency.
- **Layout:** Responsive sidebar navigation with a centered chat workspace and right-aligned document control.

### 4.2 API Client (`frontend/src/api/client.ts`)
- **Orchestration:** Handles document management, session persistence, and complex SSE streaming logic.
- **Multimodal Support:** Supports `searchByImage` for querying the document's visual database.

---

## 5. Major Features Breakdown
- **100% Offline Integrity:** Full RAG stack runs locally via Docker and Python.
- **Visual Citations:** Maps AI answers to precise document coordinates (page + bounding box).
- **Multimodal Ingestion:** Handles both native and scanned PDFs with automated diagram extraction.
- **Dynamic Context Scoping:** Allows users to focus the AI on specific documents per session.
- **Hallucination Flags:** Visual indicators in the UI for claims that lack strong source evidence.
- **Cross-Modal Retrieval:** Query the system for visual content (e.g., "Find the graph on GDP").

---

## 6. Project Directory Layout
- `/backend`: FastAPI application and RAG services.
- `/frontend`: React 19 workspace.
- `/docs`: Technical reports and design specs.
- `/models`: Local storage for model weights.
- `/volumes`: Persistent data for Milvus/PostgreSQL.
- `run.sh`: Unified startup script.
