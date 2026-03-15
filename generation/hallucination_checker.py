import numpy as np
import re
from sentence_transformers import util
from embeddings.text_embedder import embed_texts

def split_sentences(text: str) -> list[str]:
    # Basic punctuation splitting that keeps sentences reasonably intact
    # Splitting strictly on .!? might be too naïve, but works for checking sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def verify_answer(answer: str, context_chunks: list[dict], threshold: float = 0.35) -> dict:
    """
    Computes cosine similarity between generated answer sentences and context chunks.
    Flags sentences scoring below the threshold.
    """
    if not answer or not context_chunks:
        return {"verified": True, "flagged_sentences": [], "support_scores": []}
        
    sentences = split_sentences(answer)
    if not sentences:
        return {"verified": True, "flagged_sentences": [], "support_scores": []}
        
    # Gather context texts
    text_contexts = []
    for c in context_chunks:
        if c["source_type"] == "text" and "text" in c:
            text_contexts.append(c["text"])
            
    if not text_contexts:
        # If the answer was generated only from image context info, we can't text-verify easily
        return {"verified": False, "flagged_sentences": [{"sentence": "No textual context available", "max_similarity": 0.0}], "support_scores": []}

    # Embed generated sentences
    sentence_embeddings = embed_texts(sentences)
    # Embed context chunks
    context_embeddings = embed_texts(text_contexts)
    
    # Compute dot product (since already L2 normalized, dot product == cosine similarity)
    # sentence_embeddings is (N, 384), context_embeddings is (M, 384)
    # Result is (N, M)
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
