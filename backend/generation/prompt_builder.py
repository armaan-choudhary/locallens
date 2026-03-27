import re

def build_prompt(query: str, retrieved_chunks: list[dict], history: list[dict] = None) -> list[dict]:
    # Construct a RAG-optimized system prompt with numbered context excerpts
    context_parts = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        source_type = chunk.get("source_type", "text")
        if source_type == "text":
            snippet = chunk.get("text", "").strip()
            if len(snippet) > 800:
                snippet = snippet[:800] + "…"
            context_parts.append(f"[{idx}] {snippet}")
        else:
            context_parts.append(f"[{idx}] (image — no text available)")

    context_str = "\n\n".join(context_parts)
    if len(context_str) > 10_000:
        context_str = context_str[:10_000] + "\n[truncated]"

    system_content = (
        "You are a concise, factual document assistant. "
        "Answer using ONLY the numbered excerpts provided. "
        "Write plain prose. Do not use Markdown, bullet points, headings, or code blocks. "
        "Do not greet or sign off.\n\n"
        "EXCERPTS:\n"
        f"{context_str}"
    )

    messages = []

    if history:
        for turn in history[-5:]:
            messages.append({"role": turn["role"], "content": turn["content"]})

    final_query = f"{system_content}\n\nUSER QUESTION:\n{query}"
    messages.append({"role": "user", "content": final_query})

    return messages

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

_CLOSING_TRIGGERS = re.compile(
    r"(Best regards|Please (note|let|feel)|Thank you|Yours|Sincerely"
    r"|In summary[,]? I |Note that I |I hope this|LocalLens\s*\n)",
    re.IGNORECASE,
)

_SOURCE_LABEL_RE = re.compile(
    r"—\s*source:\s*\S+,\s*page\s*\d+",
    re.IGNORECASE,
)

_IMAGE_PLACEHOLDER_RE = re.compile(
    r"\[Image found on page \d+ of .*?—.*?\]",
    re.IGNORECASE,
)

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

def clean_output(text: str) -> str:
    # Remove LLM meta-commentary, thinking blocks, and formatting artifacts
    text = _THINK_BLOCK_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = _SOURCE_LABEL_RE.sub("", text)
    text = _IMAGE_PLACEHOLDER_RE.sub("", text)

    m = _CLOSING_TRIGGERS.search(text)
    if m:
        text = text[:m.start()]

    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\.\s+\.", ".", text)

    # Deduplicate repetitive sentence constructs
    sentences = re.split(r"(?<=[.!?])\s+", text)
    deduped: list[str] = []
    for s in sentences:
        if len(s) > 60 and deduped:
            norm = re.sub(r"\s+", " ", s.lower().strip())
            prev = re.sub(r"\s+", " ", deduped[-1].lower().strip())
            if norm == prev or norm in prev or prev in norm:
                continue
        deduped.append(s)
    text = " ".join(deduped)

    return text.strip()
