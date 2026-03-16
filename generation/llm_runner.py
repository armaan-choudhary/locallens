import os
from llama_cpp import Llama
from config import LLAMA_MODEL_PATH, MAX_NEW_TOKENS, TEMPERATURE
from generation.prompt_builder import clean_output

_llm = None

# ─── Tuning knobs ────────────────────────────────────────────────────
#  n_ctx      – context window; 8192 fits long RAG prompts comfortably.
#  n_batch    – tokens processed per forward pass; 512 balances VRAM vs speed.
#  n_gpu_layers – set to -1 to offload ALL layers to GPU; tune if OOM.
#  use_mlock  – pins model weights in RAM to avoid paging latency spikes.
_CTX        = 8192
_BATCH      = 512
_GPU_LAYERS = 35        # change to -1 for full GPU offload if VRAM allows
_THREADS    = 8
_USE_MLOCK  = True

_STOP_TOKENS = ["<|eot_id|>", "<|end_of_text|>"]

def get_llm() -> Llama | None:
    global _llm
    if _llm is None:
        if not os.path.exists(LLAMA_MODEL_PATH):
            print(f"[llm_runner] WARNING: model not found at {LLAMA_MODEL_PATH}")
            return None

        print(f"[llm_runner] Loading model from {LLAMA_MODEL_PATH} …")
        _llm = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_ctx=_CTX,
            n_batch=_BATCH,
            n_gpu_layers=_GPU_LAYERS,
            n_threads=_THREADS,
            use_mlock=_USE_MLOCK,
            verbose=False,
        )
        print(f"[llm_runner] Model ready  (ctx={_CTX}, batch={_BATCH}, gpu_layers={_GPU_LAYERS})")
    return _llm


def generate(messages: list) -> str:
    """Blocking single-shot generation using chat completion API."""
    llm = get_llm()
    if not llm:
        return "LLM model not loaded. Please download the Llama-3 GGUF file."

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        stop=_STOP_TOKENS,
    )
    raw = response["choices"][0]["message"]["content"].strip()
    return clean_output(raw)


def generate_stream(messages: list):
    """
    Streaming generator – yields the *cumulative* answer string after each token.
    Falls back to a single blocking call if streaming fails.
    """
    llm = get_llm()
    if not llm:
        yield "LLM model not loaded. Please download the Llama-3 GGUF file."
        return

    try:
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=_STOP_TOKENS,
            stream=True,
        )

        accumulated = ""
        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            token_text = delta.get("content", "")
            accumulated += token_text
            yield accumulated

    except Exception as exc:
        # Fall back to blocking if streaming fails
        print(f"[llm_runner] Streaming failed ({exc}), falling back to blocking generate.")
        yield generate(messages)
