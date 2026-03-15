from rank_bm25 import BM25Okapi
from storage.postgres_store import get_all_chunks
from config import TOP_K_RETRIEVAL

_bm25_index = None
_all_chunks_cache = []
_is_dirty = True

def mark_dirty():
    global _is_dirty
    _is_dirty = True

def build_index_if_needed():
    global _bm25_index, _all_chunks_cache, _is_dirty
    if _is_dirty:
        print("Rebuilding BM25 Index...")
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

def search(query: str, top_k: int = TOP_K_RETRIEVAL) -> list[dict]:
    """
    Returns text chunks matching the given BM25 keyword query.
    [{"chunk_id", "text", "page", "doc_id", "filename", "score"}, ...]
    """
    build_index_if_needed()
    if not _bm25_index or not _all_chunks_cache:
        return []
        
    query_tokens = query.lower().split()
    scores = _bm25_index.get_scores(query_tokens)
    
    # rank by scores
    top_indices = scores.argsort()[::-1][:top_k]
    
    text_results = []
    for idx in top_indices:
        score = scores[idx]
        if score > 0:
            pg_meta = _all_chunks_cache[idx]
            text_results.append({
                "chunk_id": pg_meta["chunk_id"],
                "text": pg_meta["text"],
                "page": pg_meta["page_number"],
                "doc_id": pg_meta["doc_id"],
                "filename": pg_meta["filename"],
                "score": score
            })
            
    return text_results
