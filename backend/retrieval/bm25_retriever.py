from rank_bm25 import BM25Okapi
from storage.postgres_store import get_all_chunks
from config import TOP_K_RETRIEVAL

_bm25_index = None
_all_chunks_cache = []
_is_dirty = True

def mark_dirty():
    """Mark the index as needing a rebuild."""
    global _is_dirty
    _is_dirty = True

def build_index_if_needed():
    """Build or rebuild the BM25 index from all chunks in storage."""
    global _bm25_index, _all_chunks_cache, _is_dirty
    if _is_dirty:
        _all_chunks_cache = get_all_chunks()
        
        tokenized_corpus = []
        for chunk in _all_chunks_cache:
            text = chunk.get("text", "")
            tokens = text.lower().split()
            tokenized_corpus.append(tokens)
            
        if tokenized_corpus:
            _bm25_index = BM25Okapi(tokenized_corpus)
        else:
            _bm25_index = None
        _is_dirty = False

def search(query: str, top_k: int = TOP_K_RETRIEVAL, doc_ids: list = None) -> list[dict]:
    """
    Search text chunks using BM25 keyword matching.
    """
    build_index_if_needed()
    if not _bm25_index or not _all_chunks_cache:
        return []
        
    doc_id_set = set(doc_ids) if doc_ids else None
    query_tokens = query.lower().split()
    scores = _bm25_index.get_scores(query_tokens)
    
    top_indices = scores.argsort()[::-1]
    
    text_results = []
    for idx in top_indices:
        if len(text_results) >= top_k:
            break
        score = scores[idx]
        if score > 0:
            pg_meta = _all_chunks_cache[idx]
            if doc_id_set and pg_meta["doc_id"] not in doc_id_set:
                continue
            text_results.append({
                "chunk_id": pg_meta["chunk_id"],
                "text": pg_meta["text"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "score": score
            })
            
    return text_results
