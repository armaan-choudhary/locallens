# LocalLens

## What is LocalLens
LocalLens is a fully offline, local RAG (Retrieval-Augmented Generation) system that lets users search through their own private PDFs and scanned documents — including images and diagrams — using plain natural language. It requires no cloud APIs, ensuring 100% data sovereignty and privacy.

## System Requirements
- Python 3.11+
- Tesseract installed system-wide (`sudo apt-get install tesseract-ocr`)
- Milvus running locally via Docker
- PostgreSQL running locally via Docker (or bare metal)
- NVIDIA GPU with at least 8GB VRAM recommended

## Installation

```bash
git clone https://github.com/yourteam/locallens
cd locallens
pip install -r requirements.txt

# Start Milvus
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest

# Start PostgreSQL
docker run -d --name pglocal -e POSTGRES_USER=locallens   -e POSTGRES_PASSWORD=locallens -e POSTGRES_DB=locallens   -p 5432:5432 postgres:15

# Download Llama-3 8B Q4 GGUF and place in ./models/
```

## Running the App

```bash
python main.py
```
Then open `http://localhost:7860` in your web browser.

## Architecture Overview
- **Ingestion Layer**: Extracts text via PyPDF2 and Tesseract OCR for scanned pages. Extracts images and diagrams using OpenCV edge detection.
- **Embeddings Layer**: Generates text embeddings using `all-MiniLM-L6-v2` and image embeddings using `openai/clip-vit-base-patch32`.
- **Storage Layer**: Vectors are stored in a local Milvus instance, while document metadata, text chunks, and image region coordinates are persisted in PostgreSQL.
- **Retrieval Layer**: Employs Dense vector retrieval (for both text and cross-modal image search) and BM25 sparse keyword retrieval. Results are unified and ranked using Reciprocal Rank Fusion (RRF).
- **Generation Layer**: Uses a 4-bit quantized Llama-3 (8B) model to generate responses based exclusively on top-K context. Includes a Hallucination Checker verifying generated sentences against the source context using cosine similarity.
- **Citation Layer**: Accurately traces answer details back to the specific PDF, page, and chunk/image snippet.
- **Frontend UI**: A Gradio web application for uploading and querying documents.

## Team
- Armaan (Lead Developer / AI Engineer)
- Arjun Saxena / UX UI Developer)
- Kanishk Dhiman (Data / Pipeline Engineer)
- Kartik Nagar (QA / Evaluation Specialist)
