import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from config import SBERT_MODEL_NAME

_device = "cpu"
_model = SentenceTransformer(SBERT_MODEL_NAME, device=_device)

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate L2-normalized dense embeddings for a list of strings.
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, 384)
        
    embeddings = []
    batch_size = 64
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_emb = _model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        embeddings.append(batch_emb.astype(np.float32))
        
    return np.vstack(embeddings)
