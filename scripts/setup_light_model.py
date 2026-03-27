import os
import requests
from tqdm import tqdm

def download_model():
    """
    Downloads Qwen3-Instruct-1.7B (GGUF) from Hugging Face.
    """
    model_url = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    model_path = os.path.join(model_dir, "qwen2.5-1.5b-instruct-q4_k_m.gguf")

    if os.path.exists(model_path):
        print(f"✓ Model already exists at {model_path}")
        return

    print(f"Downloading Qwen 1.5B (1.7B) model to {model_path}...")
    os.makedirs(model_dir, exist_ok=True)

    response = requests.get(model_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(model_path, "wb") as f, tqdm(
        desc="Progress",
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)

    print("\n✓ Download complete!")
    print("To use this model, update LLAMA_MODEL_PATH in backend/config.py")

if __name__ == "__main__":
    download_model()
