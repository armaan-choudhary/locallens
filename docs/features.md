# LocalLens — Feature List

A comprehensive reference of all functional capabilities in LocalLens.

---

## 🔒 Privacy & Data Sovereignty

| Feature | Description |
|---|---|
| **100% Offline Execution** | All inference, retrieval, and storage runs locally — no data ever leaves the machine. |
| **Local LLM Inference** | Uses a 4-bit quantized Llama-3 (8B) GGUF model via `llama-cpp-python` for on-device generation. |
| **Local Vector & Relational Databases** | Milvus (vector) and PostgreSQL (metadata) are self-hosted via Docker Compose. |

---

## 📄 Document Ingestion Pipeline

| Feature | Description |
|---|---|
| **PDF Text Extraction** | Extracts structured text from native PDFs using PyPDF2 and `pdf2image`. |
| **OCR for Scanned Documents** | Runs Tesseract OCR on image-based or scanned PDF pages to extract readable text. |
| **Visual Region Extraction** | Uses OpenCV to detect and crop meaningful visual regions (diagrams, charts, figures) from documents. |
| **Semantic Chunking** | Splits extracted content into semantically coherent chunks for precise retrieval. |
| **Multimodal Indexing** | Indexes both text chunks and image crops into the same unified retrieval pipeline. |

---

## 🔍 Hybrid Retrieval System

| Feature | Description |
|---|---|
| **Dense Vector Search** | Uses `all-MiniLM-L6-v2` (Sentence-Transformers) for text-to-text semantic similarity via Milvus. |
| **Cross-Modal Image Search** | Uses Open CLIP embeddings to support text-to-image retrieval across indexed visual regions. |
| **Sparse Keyword Search** | BM25 (Rank-BM25) provides exact and keyword-based retrieval coverage. |
| **Reciprocal Rank Fusion (RRF)** | Merges dense and sparse retrieval results using RRF for consistently superior accuracy. |

---

## 🤖 AI Generation & Verification

| Feature | Description |
|---|---|
| **Streaming RAG Workflow** | Generates answers incrementally using RAG, with streamed output to the frontend. |
| **Hallucination Checker** | Verifies generated responses against retrieved source chunks to flag unsupported claims. |
| **Traceable Citations** | Maps each part of the answer back to specific document pages or visual snippets. |
| **Context Management** | Maintains session-based chat history and dynamically scopes retrieval to the active document set. |

---

## 🖥️ Frontend & User Experience

| Feature | Description |
|---|---|
| **Glassmorphism Design System** | Premium React UI featuring blur-based glass aesthetics, a dark workspace, and modern typography. |
| **Document Workspace** | Upload, manage, and switch between document collections through an intuitive interface. |
| **Chat Interface** | Natural-language Q&A interface with streamed responses and inline source citations. |
| **Session History** | Persists conversation history per session for continuous, context-aware interaction. |
| **Responsive Layout** | Fully responsive React 19 + Tailwind CSS UI, built with Vite for fast HMR. |

---

## ⚙️ Infrastructure & Tooling

| Feature | Description |
|---|---|
| **One-Command Startup** | Cross-platform startup scripts (`run.sh`, `run_mac.sh`, `run.bat`) orchestrate Docker, backend, and frontend. |
| **Docker Compose Orchestration** | Manages Milvus, MinIO, etcd, and PostgreSQL services as a single local stack. |
| **FastAPI Backend** | High-performance async REST API with structured endpoints for ingestion, retrieval, and generation. |
| **LangChain Orchestration** | Chains and pipelines managed via LangChain for flexible LLM workflow composition. |
| **Automated UI Testing** | Playwright-based end-to-end test suite for frontend UX verification (`npm run test:ux`). |
| **Database Reset Utility** | Utility scripts in `/scripts` for resetting and re-initializing database state during development. |

---

## 🗂️ Supported File Types

| Type | Mechanism |
|---|---|
| Native PDFs | PyPDF2 direct text extraction |
| Scanned/Image PDFs | Tesseract OCR via pytesseract |
| Embedded Diagrams & Figures | OpenCV visual region detection + CLIP embedding |
