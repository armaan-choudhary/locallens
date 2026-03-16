MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION_TEXT = "locallens_text"
MILVUS_COLLECTION_IMAGE = "locallens_image"

POSTGRES_DSN = "postgresql://locallens:locallens@localhost:5432/locallens"

# Local model paths and model identifiers
LLAMA_MODEL_PATH = "./models/Qwen3-8B-Q4_K_M.gguf"
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
