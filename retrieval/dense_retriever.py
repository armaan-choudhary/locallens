from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_text_for_image
from storage.milvus_store import search_text, search_image
from storage.postgres_store import get_chunk_by_milvus_id, get_image_by_milvus_id
from config import TOP_K_RETRIEVAL

def run_dense_retrieval(query: str):
    """
    Search Milvus for text and image embeddings.
    Returns: (text_results, image_results)
    text_results: [{"chunk_id", "text", "page", "doc_id", "score"}, ...]
    image_results: [{"image_id", "page", "doc_id", "bbox", "score", "nearby_chunk_id"}, ...]
    """
    if not query.strip():
        return [], []
        
    text_emb = embed_texts([query])
    image_emb = embed_text_for_image(query)
    
    milvus_text_res = search_text(text_emb, TOP_K_RETRIEVAL)
    milvus_image_res = search_image(image_emb, TOP_K_RETRIEVAL)
    
    text_results = []
    for hit in milvus_text_res:
        m_id = hit["milvus_id"]
        pg_meta = get_chunk_by_milvus_id(m_id)
        if pg_meta:
            text_results.append({
                "chunk_id": pg_meta["chunk_id"],
                "text": pg_meta["text"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "score": hit["score"]
            })
            
    image_results = []
    for hit in milvus_image_res:
        m_id = hit["milvus_id"]
        pg_meta = get_image_by_milvus_id(m_id)
        if pg_meta:
            bbox = [pg_meta["bbox_x1"], pg_meta["bbox_y1"], pg_meta["bbox_x2"], pg_meta["bbox_y2"]]
            image_results.append({
                "image_id": pg_meta["image_id"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "bbox": bbox,
                "nearby_chunk_id": pg_meta["nearby_chunk_id"],
                "score": hit["score"]
            })
            
    return text_results, image_results
