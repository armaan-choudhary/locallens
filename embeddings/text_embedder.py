import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from config import SBERT_MODEL_NAME

# Load model once at module level
print(f"Loading SentenceTransformer model: {SBERT_MODEL_NAME}")
_device = "cuda" if torch.cuda.is_available() else "cpu"
_model = SentenceTransformer(SBERT_MODEL_NAME, device=_device)

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate L2-normalized dense embeddings for a list of strings.
    Batched in groups of 64 for memory efficiency.
    Returns: float32 numpy array of shape (N, 384)
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, 384)
        
    embeddings = []
    batch_size = 64
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # SentenceTransformer encode computes L2 normalized if normalize_embeddings=True
        # Or we can do it manually, though SBERT models usually return somewhat normalized or we just normalize it.
        # We'll explicitly normalize to be safe.
        batch_emb = _model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        embeddings.append(batch_emb.astype(np.float32))
        
    all_embeddings = np.vstack(embeddings)
    
    return all_embeddings
