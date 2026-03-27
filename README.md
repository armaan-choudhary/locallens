# LocalLens

LocalLens is a high-performance, privacy-first Retrieval-Augmented Generation (RAG) system designed for local document intelligence. It enables users to interact with their private document collections (PDFs, scanned images, and diagrams) using natural language, all while maintaining 100% data sovereignty by running entirely offline.

## Key Features

- **Privacy-First Architecture**: Fully local execution using 4-bit quantized Llama-3 (8B) and local vector/relational databases.
- **Multimodal Ingestion**: Automated pipeline for text extraction (PyPDF2), OCR for scanned documents (Tesseract), and visual region extraction (OpenCV).
- **Hybrid Retrieval System**: Combines Dense vector retrieval (CLIP/MiniLM) with Sparse keyword search (BM25), unified via Reciprocal Rank Fusion (RRF) for superior accuracy.
- **Premium User Experience**: Modern React-based interface featuring a glassmorphism design system for a sleek, responsive workspace.
- **Traceable Citations**: High-fidelity citation mapping that links generated answers directly to specific document pages and visual snippets.
- **Context Management**: Session-based chat history with dynamic document scoping for focused information retrieval.

## System Requirements

- **Operating System**: Linux (developed and tested on PopOS)
- **Runtime**: Python 3.11+ and Node.js 18+
- **Database**: Docker installed (for Milvus and PostgreSQL)
- **Hardware**: NVIDIA GPU with 8GB+ VRAM recommended for optimal inference speeds.
- **System Dependencies**: Tesseract OCR (`sudo apt-get install tesseract-ocr`)

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/locallens
   cd locallens
   ```

2. **Backend Setup**:
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Initialize Models**:
   Place the Llama-3 8B GGUF model in the `./models/` directory.

## Running the Application

The simplest way to start the entire stack is using the provided startup scripts:

- **Linux/macOS**: `./run.sh` (or `run_mac.sh`)
- **Windows**: `run.bat`

Ensure you give execution permissions on Unix systems: `chmod +x run.sh run_mac.sh`.

These scripts orchestrate the following:
- **Database Services**: Starts Milvus and PostgreSQL via Docker Compose.
- **Backend API**: Launches the FastAPI server (from `/backend`) at `http://localhost:8000`.
- **Frontend UI**: Starts the Vite development server (from `/frontend`) at `http://localhost:5173`.

## Project Structure

- **`backend/`**: Core FastAPI application, ingestion services, and storage logic.
- **`frontend/`**: React 19 + Tailwind CSS user interface.
- **`docs/`**: Project documentation, design PDFs, and tech stack reports.
- **`scripts/`**: Utility scripts like database resets.
- **`models/`**: Local LLM and embedding model weights.

## Architecture Overview

- **Ingestion**: Pre-processes documents into semantic chunks and visual crops.
- **Embeddings**: Utilizes `all-MiniLM-L6-v2` for text and `CLIP` for cross-modal image search.
- **Storage**: Vector data is managed in **Milvus**, while metadata and chat history are persisted in **PostgreSQL**.
- **Generation**: Implements a streaming RAG workflow with an integrated hallucination checker for response verification.

## Development & Testing

LocalLens uses **Playwright** for automated UI and UX verification.
```bash
cd frontend
npm run test:ux
```

## Team
- **Armaan**: Lead Developer / AI Engineer
- **Arjun Saxena**: UI/UX Developer
- **Kanishk Dhiman**: Data Pipeline Engineer
- **Kartik Nagar**: QA / Evaluation Specialist
