import os
import re
from llama_cpp import Llama
from config import LLAMA_MODEL_PATH, MAX_NEW_TOKENS, TEMPERATURE
from generation.prompt_builder import clean_output

_llm = None

# Hardware-specific llama-cpp parameters
_CTX        = 4096
_BATCH      = 512
_GPU_LAYERS = -1        # -1 offloads all layers to GPU (Best for 1B-8B models)
_THREADS    = 6
_USE_MLOCK  = True

_STOP_TOKENS = ["<|im_end|>", "<|end_of_text|>", "<end_of_turn>", "<eos>"]

def get_llm() -> Llama | None:
    # Lazy initialization of the LLAMA model with GPU acceleration
    global _llm
    if _llm is None:
        if not os.path.exists(LLAMA_MODEL_PATH):
            return None

        _llm = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_ctx=_CTX,
            n_batch=_BATCH,
            n_gpu_layers=_GPU_LAYERS,
            n_threads=_THREADS,
            use_mlock=_USE_MLOCK,
            flash_attn=True,
            verbose=False,
        )
    return _llm

def generate(messages: list) -> str:
    # Standard inference for non-streaming workloads
    llm = get_llm()
    if not llm:
        return "Model not loaded. Please verify the model path."

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        top_p=0.95,
        top_k=20,
        repeat_penalty=1.1,
        stop=_STOP_TOKENS,
    )
    raw = response["choices"][0]["message"]["content"].strip()
    return clean_output(raw)

def generate_stream(messages: list):
    # Streaming inference with real-time <think> block removal
    llm = get_llm()
    if not llm:
        yield "Model not loaded. Please verify the model path."
        return

    try:
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.95,
            top_k=20,
            repeat_penalty=1.1,
            stop=_STOP_TOKENS,
            stream=True,
        )

        accumulated = ""
        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            token_text = delta.get("content", "")
            accumulated += token_text
            
            display_text = accumulated
            if "<think>" in display_text:
                if "</think>" in display_text:
                    display_text = re.sub(r"<think>.*?</think>", "", display_text, flags=re.DOTALL)
                else:
                    display_text = display_text.split("<think>")[0]
            
            yield display_text.strip()

    except Exception as exc:
        yield generate(messages)
