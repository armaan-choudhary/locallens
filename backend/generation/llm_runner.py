import os
import re
import ctypes
from llama_cpp import Llama
from config import LLAMA_MODEL_PATH, MAX_NEW_TOKENS, TEMPERATURE, LLM_MIN_FREE_RAM_GB
from generation.prompt_builder import clean_output

_llm = None

# Hardware-specific llama-cpp parameters
_CTX        = 4096
_BATCH      = 512
_GPU_LAYERS = -1        # Offload completely to GPU to fix latency issues
_THREADS    = 12
_USE_MLOCK  = False

_STOP_TOKENS = ["<|im_end|>", "<|end_of_text|>", "<end_of_turn>", "<eos>"]

def _has_min_available_ram(min_free_gb: float = 3.0) -> bool:
    """Best-effort RAM availability check to avoid unstable model initialization."""
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return True

        avail_gb = status.ullAvailPhys / (1024 ** 3)
        return avail_gb >= min_free_gb
    except Exception:
        return True

def get_llm() -> Llama | None:
    # Lazy initialization of the LLAMA model with GPU acceleration
    global _llm
    if _llm is None:
        if not os.path.exists(LLAMA_MODEL_PATH):
            print(f"ERROR: Model path does not exist: {LLAMA_MODEL_PATH}")
            return None

        print(f"DEBUG: Loading model from {LLAMA_MODEL_PATH}")
        
        try:
            _llm = Llama(
                model_path=LLAMA_MODEL_PATH,
                n_ctx=_CTX,
                n_batch=_BATCH,
                n_gpu_layers=_GPU_LAYERS,
                n_threads=_THREADS,
                use_mlock=_USE_MLOCK,
                flash_attn=False,
                verbose=False,
            )
        except Exception as e:
            print(f"ERROR: Failed to load model: {e}")
            return None
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
