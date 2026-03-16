import numpy as np
import re
from embeddings.text_embedder import embed_texts

def split_sentences(text: str) -> list[str]:
    # Segment text into discrete sentences for granular verification
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def verify_answer(answer: str, context_chunks: list[dict], threshold: float = 0.35) -> dict:
    # Cross-reference generated text against context chunks using cosine similarity
    if not answer or not context_chunks:
        return {"verified": True, "flagged_sentences": [], "support_scores": []}
        
    sentences = split_sentences(answer)
    if not sentences:
        return {"verified": True, "flagged_sentences": [], "support_scores": []}
        
    text_contexts = []
    for c in context_chunks:
        if c["source_type"] == "text" and "text" in c:
            text_contexts.append(c["text"])
            
    if not text_contexts:
        return {"verified": False, "flagged_sentences": [{"sentence": "No textual context available", "max_similarity": 0.0}], "support_scores": []}

    # Embed both generated sentences and source context for similarity scoring
    sentence_embeddings = embed_texts(sentences)
    context_embeddings = embed_texts(text_contexts)
    
    # Calculate similarity matrix via dot product (normalized embeddings)
    similarities = np.dot(sentence_embeddings, context_embeddings.T)
    max_similarities = similarities.max(axis=1)
    
    flagged_sentences = []
    support_scores = []
    verified = True
    
    for i, max_sim in enumerate(max_similarities):
        sentence = sentences[i]
        sim_score = float(max_sim)
        
        support_scores.append({
            "sentence": sentence,
            "score": sim_score
        })
        
        if sim_score < threshold:
            verified = False
            flagged_sentences.append({
                "sentence": sentence,
                "max_similarity": sim_score
            })
            
    return {
        "answer": answer,
        "verified": verified,
        "flagged_sentences": flagged_sentences,
        "support_scores": support_scores
    }
