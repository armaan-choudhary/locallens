def build_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Constructs a structured prompt for the LLM using the provided context chunks.
    Ensures context stays under ~3500 tokens.
    """
    
    context_lines = []
    
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        source_name = chunk.get("filename", "Unknown Document")
        page_num = chunk.get("page", "?")
        
        if chunk["source_type"] == "text":
            text_snippet = chunk.get("text", "")
            context_lines.append(f"[{text_snippet} — source: {source_name}, page {page_num}]")
        elif chunk["source_type"] == "image":
            # For images, we provide a placeholder note that an image was retrieved
            # The UI will display the actual image citation.
            context_lines.append(f"[Image found on page {page_num} of {source_name} — see citation for context]")
            
    context_str = "\n".join(context_lines)
    
    # Optional truncation to prevent blowing up the context window
    # Rough heuristic: 1 char ~ 0.25 tokens
    if len(context_str) > 12000:
        context_str = context_str[:12000] + "...\n[Context truncated]"
        
    prompt = f"""You are LocalLens, a precise document assistant. Answer the question using ONLY the context provided below. If the answer is not in the context, say so clearly. Do not make up information.

CONTEXT:
{context_str}

QUESTION: {query}

ANSWER:
"""
    return prompt
