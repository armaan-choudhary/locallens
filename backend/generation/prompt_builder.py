import re

def build_prompt(query: str, retrieved_chunks: list[dict], history: list[dict] = None) -> list[dict]:
    # Construct a RAG-optimized system prompt with numbered context excerpts
    context_parts = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        source_type = chunk.get("source_type", "text")
        filename = chunk.get("filename", "Unknown")
        page_num = chunk.get("page_number", "?")
        
        if source_type == "text":
            snippet = chunk.get("text", "").strip()
            if len(snippet) > 800:
                snippet = snippet[:800] + "…"
            context_parts.append(f"[{idx}] From {filename} (page {page_num}): {snippet}")
        else:
            context_parts.append(f"[{idx}] From {filename} (page {page_num}): (image — no text available)")

    context_str = "\n\n".join(context_parts)
    # Allow full context without aggressive truncation
    # Model can handle up to 10k tokens, let it use more context for better answers


    system_content = (
        "You are a precise, factual document assistant. Your role is to answer questions "
        "ONLY using the information in the numbered excerpts below. "
        "Follow these rules STRICTLY:\n\n"
        "1. ONLY use information explicitly stated in the excerpts.\n"
        "2. DO NOT infer, assume, or generate any information not in the excerpts.\n"
        "3. DO NOT use your training data to fill gaps.\n"
        "4. If the answer is not in the excerpts, respond with: "
        "'I don't have this information in the provided documents.'\n"
        "5. Write in plain prose. Do not use Markdown, bullet points, headings, or code blocks.\n"
        "6. Do not greet, sign off, or add meta-commentary.\n\n"
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
    r"(Best regards[,\.]?|Yours (sincerely|faithfully)?|Sincerely[,\.]?|"
    r"Thank you[,\.]?|Respectfully|Warm regards)",
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
    if m and m.start() > len(text) * 0.8:  # Only truncate if match is in last 20% of text
        text = text[:m.start()]

    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\.\s+\.", ".", text)

    # Deduplicate ONLY exact repeats, not elaborations
    sentences = re.split(r"(?<=[.!?])\s+", text)
    deduped: list[str] = []
    for s in sentences:
        if len(s) > 60 and deduped:
            norm = re.sub(r"\s+", " ", s.lower().strip())
            prev = re.sub(r"\s+", " ", deduped[-1].lower().strip())
            # Only skip if sentences are EXACTLY the same (not substring matches)
            if norm == prev:
                continue
        deduped.append(s)
    text = " ".join(deduped)

    return text.strip()
