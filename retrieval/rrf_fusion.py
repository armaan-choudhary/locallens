from config import TOP_K_FINAL

def rrf_fusion(text_dense: list[dict], image_dense: list[dict], text_bm25: list[dict], text_weights=(1.0, 1.0, 1.0)) -> list[dict]:
    """
    Reciprocal Rank Fusion with formula: sum(1 / (k + rank))
    Deduplicates by chunk_id/image_id.
    Returns merged top_k_final results.
    Each result carries source_type, score, and original metadata.
    """
    K = 60
    scores_dict = {}
    details_dict = {}

    def process_list(results, prefix, source_type):
        """Rank starts at 1"""
        for rank, res in enumerate(results, start=1):
            
            # for text, key is 'text:chunk_id'
            # for image, key is 'image:image_id'
            if source_type == "text":
                uid = res["chunk_id"]
                key = f"text:{uid}"
            else:
                uid = res["image_id"]
                key = f"image:{uid}"
                
            score = 1.0 / (K + rank)
            
            if key not in scores_dict:
                scores_dict[key] = 0.0
                # Copy properties
                item = {"source_type": source_type}
                item.update(res)
                details_dict[key] = item
                
            scores_dict[key] += score

    # Process each list
    process_list(text_dense, "dt", "text")
    process_list(image_dense, "di", "image")
    process_list(text_bm25, "bt", "text")
    
    # Update items with RRF score and sort
    final_list = []
    for key, rrf_score in scores_dict.items():
        item = details_dict[key]
        item["rrf_score"] = rrf_score
        final_list.append(item)
        
    final_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    
    return final_list[:TOP_K_FINAL]
