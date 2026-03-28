import torch
import open_clip
import numpy as np
import os
import shutil
from PIL import Image
from config import CLIP_MODEL_NAME

_device = "cpu" 
_model_name = "ViT-B-32"
_pretrained = "openai"

_model = None
_preprocess = None
_tokenizer = None

def _has_min_free_space(min_free_gb: float = 2.0) -> bool:
    """Return True if the Hugging Face cache drive has enough free space."""
    hf_home = os.getenv("HF_HOME")
    if hf_home:
        probe_path = hf_home
    else:
        user_home = os.path.expanduser("~")
        probe_path = os.path.join(user_home, ".cache", "huggingface")

    if not os.path.exists(probe_path):
        probe_path = os.path.expanduser("~")

    usage = shutil.disk_usage(probe_path)
    free_gb = usage.free / (1024 ** 3)
    return free_gb >= min_free_gb

def get_resources():
    global _model, _preprocess, _tokenizer
    if _model is None:
        if not _has_min_free_space(2.0):
            raise RuntimeError("Insufficient disk space for CLIP model cache; skipping image embedding.")
        _model, _, _preprocess = open_clip.create_model_and_transforms(_model_name, pretrained=_pretrained, device=_device)
        _tokenizer = open_clip.get_tokenizer(_model_name)
    return _model, _preprocess, _tokenizer

def embed_images(images: list[Image.Image]) -> np.ndarray:
    """
    Generate L2-normalized dense embeddings for a list of PIL Images.
    """
    if not images:
        return np.array([], dtype=np.float32).reshape(0, 512)
        
    model, preprocess, _ = get_resources()
    model.eval()
    batch_size = 8
    embeddings = []
    
    with torch.no_grad():
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            tensor_batch = torch.stack([preprocess(img) for img in batch]).to(_device)
            image_features = model.encode_image(tensor_batch)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            embeddings.append(image_features.cpu().numpy().astype(np.float32))
            
    return np.vstack(embeddings)

def embed_text_for_image(query: str) -> np.ndarray:
    """
    Encode a text string into CLIP's shared embedding space for cross-modal retrieval.
    """
    if not query:
        return np.zeros((1, 512), dtype=np.float32)
        
    model, _, tokenizer = get_resources()
    model.eval()
    with torch.no_grad():
        text_tokens = tokenizer([query]).to(_device)
        text_features = model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        
    return text_features.cpu().numpy().astype(np.float32)
