from config import TOP_K_FINAL

def rrf_fusion(text_dense: list[dict], image_dense: list[dict], text_bm25: list[dict], text_weights=(1.2, 1.0, 0.8)) -> list[dict]:
    """
    Perform Reciprocal Rank Fusion to merge and deduplicate search results.
    """
    K = 60
    scores_dict = {}
    details_dict = {}

    def process_list(results, prefix, source_type, weight=1.0):
        for rank, res in enumerate(results, start=1):
            if source_type == "text":
                uid = res["chunk_id"]
                key = f"text:{uid}"
            else:
                uid = res["image_id"]
                key = f"image:{uid}"
                
            score = (1.0 / (K + rank)) * weight
            
            if key not in scores_dict:
                scores_dict[key] = 0.0
                item = {"source_type": source_type}
                item.update(res)
                details_dict[key] = item
                
            scores_dict[key] += score

    process_list(text_dense, "dt", "text", weight=text_weights[0])
    process_list(image_dense, "di", "image", weight=text_weights[1])
    process_list(text_bm25, "bt", "text", weight=text_weights[2])
    
    final_list = []
    for key, rrf_score in scores_dict.items():
        item = details_dict[key]
        item["rrf_score"] = rrf_score
        final_list.append(item)
        
    final_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    
    return final_list[:TOP_K_FINAL]
