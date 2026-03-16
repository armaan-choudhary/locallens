import re

# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(query: str, retrieved_chunks: list[dict], history: list[dict] = None) -> list[dict]:
    """
    Build a list of chat messages for create_chat_completion.
    Context excerpts are numbered [1], [2]... so the LLM cannot echo raw filenames.
    Injections multi-turn history (last 5 turns) for context continuity.
    """
    context_parts = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        # retrieved_chunks might contain 'source_type' or we infer it
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

    messages = [{"role": "system", "content": system_content}]

    # Inject multi-turn history
    if history:
        for turn in history[-5:]:
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Current user query
    messages.append({"role": "user", "content": query})

    return messages


# ── Post-processor ────────────────────────────────────────────────────────────

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

# Patterns that signal the LLM started a closing or meta-commentary block
_CLOSING_TRIGGERS = re.compile(
    r"(Best regards|Please (note|let|feel)|Thank you|Yours|Sincerely"
    r"|In summary[,]? I |Note that I |I hope this|LocalLens\s*\n)",
    re.IGNORECASE,
)

# Source-label leaks the LLM sometimes echoes back verbatim
_SOURCE_LABEL_RE = re.compile(
    r"—\s*source:\s*\S+,\s*page\s*\d+",
    re.IGNORECASE,
)

_IMAGE_PLACEHOLDER_RE = re.compile(
    r"\[Image found on page \d+ of .*?—.*?\]",
    re.IGNORECASE,
)


def clean_output(text: str) -> str:
    """
    Strip emojis, source-label echoes, image placeholders, letter closings,
    and deduplicate repeated paragraphs.
    """
    # 1. Remove emojis
    text = _EMOJI_RE.sub("", text)

    # 2. Strip raw source labels that leaked through
    text = _SOURCE_LABEL_RE.sub("", text)

    # 3. Strip image placeholder echoes
    text = _IMAGE_PLACEHOLDER_RE.sub("", text)

    # 4. Cut at the first closing / meta-commentary marker
    m = _CLOSING_TRIGGERS.search(text)
    if m:
        text = text[:m.start()]

    # 5. Collapse whitespace artefacts
    text = re.sub(r"[ \t]{2,}", " ", text)        # multiple spaces → one
    text = re.sub(r"\n{3,}", "\n\n", text)         # 3+ blank lines → 2
    text = re.sub(r"\.\s+\.", ".", text)            # double period

    # 6. Deduplicate consecutive near-identical sentences (>60 chars)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    deduped: list[str] = []
    for s in sentences:
        if len(s) > 60 and deduped:
            # compare normalised versions
            norm = re.sub(r"\s+", " ", s.lower().strip())
            prev = re.sub(r"\s+", " ", deduped[-1].lower().strip())
            if norm == prev or norm in prev or prev in norm:
                continue
        deduped.append(s)
    text = " ".join(deduped)

    return text.strip()
