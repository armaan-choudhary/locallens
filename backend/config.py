import os
from dotenv import load_dotenv

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
MILVUS_COLLECTION_TEXT = os.getenv("MILVUS_COLLECTION_TEXT", "locallens_text")
MILVUS_COLLECTION_IMAGE = os.getenv("MILVUS_COLLECTION_IMAGE", "locallens_image")

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://locallens:locallens@localhost:5432/locallens")

# Project Root (one level up from backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Local model paths (choose one)
# Performance: Gemma 3 1B Q4_0 (~1GB)
LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "gemma-3-1b-it-q4_0.gguf")

# Optional: Gemma 3 1B f16 (~2GB)
# LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "gemma-3-1b-it-f16.gguf")

# Standard: Qwen3-8B (~5GB)
# LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "Qwen3-8B-Q4_K_M.gguf")

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# Ingestion and retrieval tuning
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_RETRIEVAL = 10
TOP_K_FINAL = 3

# Inference parameters
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.6
TARGET_LATENCY_SECONDS = 15

# Storage and Path Configurations
INGEST_TEMP_DIR = "/tmp/locallens_ingest"
STORAGE_IMAGES_DIR = os.path.join(PROJECT_ROOT, "backend", "storage", "images")
