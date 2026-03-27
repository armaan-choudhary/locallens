# LocalLens Technology Stack Report

## Overview
LocalLens is a private, offline document AI system designed for multimodal RAG (Retrieval-Augmented Generation). It enables users to index PDFs (text and images) and query them using a local LLM with verified citations.

## Core Technology Stack

### 1. Backend & AI Orchestration
- **Language:** [Python 3.x](https://www.python.org/)
- **API Framework:** [FastAPI](https://fastapi.tiangolo.com/) - High-performance web framework for building APIs.
- **Orchestration:** [LangChain](https://www.langchain.com/) - Framework for developing applications powered by large language models.

### 2. Frontend (Modern Web UI)
- **Framework:** [React 19](https://react.dev/) - A JavaScript library for building user interfaces.
- **Build Tool:** [Vite](https://vitejs.dev/) - Next-generation frontend tooling.
- **Language:** [TypeScript](https://www.typescriptlang.org/) - Typed superset of JavaScript.
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework.
- **Routing:** [React Router 6](https://reactrouter.com/) - Declarative routing for React.
- **Icons:** [Lucide React](https://lucide.dev/) - Beautiful & consistent icons.
- **HTTP Client:** [Axios](https://axios-http.com/) - Promise-based HTTP client for the browser and node.js.

### 3. Databases & Storage
- **Vector Database:** [Milvus](https://milvus.io/) - Open-source vector database built for AI applications.
- **Relational Database:** [PostgreSQL 15](https://www.postgresql.org/) - Robust metadata and document storage.
- **Object Storage:** [MinIO](https://min.io/) - High-performance, S3-compatible object storage (used by Milvus).
- **Service Coordination:** [etcd](https://etcd.io/) - Distributed reliable key-value store (used by Milvus).

### 4. Artificial Intelligence & NLP
- **Large Language Model:** [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) - Local LLM inference (GGUF support).
- **Text Embeddings:** [Sentence-Transformers](https://www.sbert.net/) - State-of-the-art text and image embeddings.
- **Multimodal Embeddings:** [Open CLIP](https://github.com/mlfoundations/open_clip) - Open-source implementation of CLIP (Contrastive Language-Image Pre-training).
- **Deep Learning Framework:** [PyTorch](https://pytorch.org/) - Core framework for machine learning.

### 5. Document & Image Processing
- **PDF Extraction:** [PyPDF2](https://pypdf2.readthedocs.io/) & [pdf2image](https://github.com/Belval/pdf2image)
- **OCR (Optical Character Recognition):** [Tesseract (pytesseract)](https://github.com/madmaze/pytesseract)
- **Image Processing:** [Pillow (PIL)](https://python-pillow.org/) & [OpenCV (opencv-python-headless)](https://opencv.org/)
- **Search Algorithms:** [Rank-BM25](https://github.com/dorianbrown/rank-bm25) - Sparse retrieval (BM25) implementation.

### 6. Infrastructure & Tooling
- **Containerization:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) - Container orchestration for local deployment.
- **Testing:** [Playwright](https://playwright.dev/) - End-to-end testing for the frontend.
- **Static Analysis:** [ESLint](https://eslint.org/) & [TypeScript](https://www.typescriptlang.org/)
- **Utility Libraries:** [NumPy](https://numpy.org/), [Pydantic](https://docs.pydantic.dev/), [tqdm](https://github.com/tqdm/tqdm)

## Project Organization
LocalLens is organized for high modularity:
- **`/backend`**: Encapsulates all Python logic, API routes, and RAG services.
- **`/frontend`**: Contains the React-based workspace.
- **`/docs`**: Centralized repository for design and technical documentation.
- **`/scripts`**: Management and maintenance utilities.

## Summary of Architecture
LocalLens uses a **Hybrid Retrieval** approach combining dense vector search (Milvus) with sparse keyword search (BM25), fused using **Reciprocal Rank Fusion (RRF)**. It features a multimodal pipeline that indexes both text chunks and image regions (via OCR and CLIP), ensuring comprehensive document understanding entirely offline.
