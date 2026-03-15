# config.py — all tunable parameters live here

MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION_TEXT = "locallens_text"
MILVUS_COLLECTION_IMAGE = "locallens_image"

POSTGRES_DSN = "postgresql://locallens:locallens@localhost:5432/locallens"

LLAMA_MODEL_PATH = "./models/llama3-8b-q4.gguf"  # path to local GGUF file
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 512        # characters per text chunk
CHUNK_OVERLAP = 64      # overlap between consecutive chunks
TOP_K_RETRIEVAL = 10    # number of results to fetch per retriever before RRF
TOP_K_FINAL = 5         # final top results passed to LLM after RRF
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.1
TARGET_LATENCY_SECONDS = 15
