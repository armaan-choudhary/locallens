import torch
import open_clip
import numpy as np
from PIL import Image
from config import CLIP_MODEL_NAME

_device = "cpu" 
_model_name = "ViT-B-32"
_pretrained = "openai"

_model, _, _preprocess = open_clip.create_model_and_transforms(_model_name, pretrained=_pretrained, device=_device)
_tokenizer = open_clip.get_tokenizer(_model_name)

def embed_images(images: list[Image.Image]) -> np.ndarray:
    """
    Generate L2-normalized dense embeddings for a list of PIL Images.
    """
    if not images:
        return np.array([], dtype=np.float32).reshape(0, 512)
        
    embeddings = []
    batch_size = 32
    _model.eval()
    
    with torch.no_grad():
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            tensor_batch = torch.stack([_preprocess(img) for img in batch]).to(_device)
            image_features = _model.encode_image(tensor_batch)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            embeddings.append(image_features.cpu().numpy().astype(np.float32))
            
    return np.vstack(embeddings)

def embed_text_for_image(query: str) -> np.ndarray:
    """
    Encode a text string into CLIP's shared embedding space for cross-modal retrieval.
    """
    if not query:
        return np.zeros((1, 512), dtype=np.float32)
        
    _model.eval()
    with torch.no_grad():
        text_tokens = _tokenizer([query]).to(_device)
        text_features = _model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        
    return text_features.cpu().numpy().astype(np.float32)
