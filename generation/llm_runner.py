import os
from llama_cpp import Llama
from config import LLAMA_MODEL_PATH, MAX_NEW_TOKENS, TEMPERATURE

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        if not os.path.exists(LLAMA_MODEL_PATH):
            print(f"WARNING: LLM model not found at {LLAMA_MODEL_PATH}")
            return None
            
        print(f"Loading LLM from {LLAMA_MODEL_PATH}")
        _llm = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=35,
            n_threads=8,
            verbose=False
        )
    return _llm

def generate(prompt: str) -> str:
    """Generate answer from Llama-3"""
    llm = get_llm()
    if not llm:
        return "LLM model not loaded. Please download the Llama-3 GGUF file."
        
    response = llm(
        prompt, 
        max_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE, 
        stop=["</s>", "Human:", "User:", "<|eot_id|>"]
    )
    
    return response["choices"][0]["text"].strip()
