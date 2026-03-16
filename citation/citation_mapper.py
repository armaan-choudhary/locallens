def map_citations(final_answer: str, ranked_chunks: list[dict]) -> list[dict]:
    """
    Map context chunks to citation cards for the generated answer.
    """
    if not ranked_chunks:
        return []
        
    citation_cards = []
    
    for chunk in ranked_chunks:
        source_type = chunk.get("source_type")
        
        card = {
            "doc_name": chunk.get("filename", "Unknown Document"),
            "page_number": chunk.get("page", 1),
            "source_type": source_type
        }
        
        if source_type == "text":
            card["chunk_text"] = chunk.get("text", "")
            card["char_start"] = chunk.get("char_start", 0)
            card["char_end"] = chunk.get("char_end", 0)
            card["bbox"] = None
        else:
            card["chunk_text"] = "Image Region Extracted"
            card["char_start"] = 0
            card["char_end"] = 0
            card["image_id"] = chunk.get("image_id")
            card["bbox"] = chunk.get("bbox", [0, 0, 0, 0])
                
        citation_cards.append(card)
        
    return citation_cards
