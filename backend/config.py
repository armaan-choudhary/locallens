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
# Standard: Qwen3-8B (~5GB)
LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "Qwen3-8B-Q4_K_M.gguf")

# Lightweight: Qwen2.5-1.5B (~1.2GB) - Faster but slightly less accurate
# LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# Ingestion and retrieval tuning
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_RETRIEVAL = 10
TOP_K_FINAL = 3

# Inference parameters
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.6
TARGET_LATENCY_SECONDS = 15

# Storage and Path Configurations
INGEST_TEMP_DIR = "/tmp/locallens_ingest"
STORAGE_IMAGES_DIR = os.path.join(PROJECT_ROOT, "backend", "storage", "images")
