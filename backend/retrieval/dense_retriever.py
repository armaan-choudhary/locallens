import asyncio
from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_text_for_image
from storage.milvus_store import search_text, search_image
from storage.postgres_store import get_chunk_by_milvus_id, get_image_by_milvus_id
from config import TOP_K_RETRIEVAL

async def run_dense_retrieval_async(query: str, doc_ids: list = None):
    """
    Perform asynchronous dense retrieval for both text and image modalities.
    """
    if not query.strip():
        return [], []
        
    loop = asyncio.get_event_loop()
    
    # Generate embeddings
    text_emb = await loop.run_in_executor(None, embed_texts, [query])
    image_emb = None
    try:
        image_emb = await loop.run_in_executor(None, embed_text_for_image, query)
    except Exception as e:
        print(f"Warning: image embedding unavailable, continuing with text-only retrieval: {e}")
    
    # Concurrent vector searches
    text_task = loop.run_in_executor(None, search_text, text_emb, TOP_K_RETRIEVAL, doc_ids)
    milvus_text_res = await text_task

    if image_emb is not None:
        try:
            image_task = loop.run_in_executor(None, search_image, image_emb, TOP_K_RETRIEVAL, doc_ids)
            milvus_image_res = await image_task
        except Exception as e:
            print(f"Warning: image retrieval failed, continuing with text-only results: {e}")
            milvus_image_res = []
    else:
        milvus_image_res = []
    
    async def get_text_meta(hit):
        m_id = hit["milvus_id"]
        pg_meta = await loop.run_in_executor(None, get_chunk_by_milvus_id, m_id)
        if pg_meta:
            return {
                "chunk_id": pg_meta["chunk_id"],
                "text": pg_meta["text"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "score": hit["score"]
            }
        return None

    async def get_image_meta(hit):
        m_id = hit["milvus_id"]
        pg_meta = await loop.run_in_executor(None, get_image_by_milvus_id, m_id)
        if pg_meta:
            bbox = [pg_meta["bbox_x1"], pg_meta["bbox_y1"], pg_meta["bbox_x2"], pg_meta["bbox_y2"]]
            return {
                "image_id": pg_meta["image_id"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "bbox": bbox,
                "nearby_chunk_id": pg_meta["nearby_chunk_id"],
                "image_path": pg_meta.get("image_path"),
                "score": hit["score"]
            }
        return None

    text_meta_tasks = [get_text_meta(hit) for hit in milvus_text_res]
    image_meta_tasks = [get_image_meta(hit) for hit in milvus_image_res]
    
    text_results_raw = await asyncio.gather(*text_meta_tasks)
    image_results_raw = await asyncio.gather(*image_meta_tasks)
    
    text_results = [r for r in text_results_raw if r]
    image_results = [r for r in image_results_raw if r]
            
    return text_results, image_results

def run_dense_retrieval(query: str, doc_ids: list = None):
    """Synchronous wrapper for dense retrieval."""
    return asyncio.run(run_dense_retrieval_async(query, doc_ids))
