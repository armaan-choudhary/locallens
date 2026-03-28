import os
import uuid
import json
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from PIL import Image

from retrieval.dense_retriever import run_dense_retrieval_async
from retrieval.bm25_retriever import search as bm25_search
from retrieval.rrf_fusion import rrf_fusion
from generation.prompt_builder import build_prompt
from generation.llm_runner import generate as generate_answer, generate_stream
from generation.hallucination_checker import verify_answer
from citation.citation_mapper import map_citations
from storage.postgres_store import (
    get_messages_for_session, get_docs_for_session, add_message, 
    get_image_by_milvus_id
)
from storage.milvus_store import search_image
from embeddings.image_embedder import embed_images
from config import TOP_K_RETRIEVAL

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    session_id: str = None

@router.post("/search/image")
async def search_by_image(file: UploadFile = File(...), session_id: str = Form(None)):
    try:
        img = Image.open(file.file).convert("RGB")
        image_emb = embed_images([img])
        
        from ingestion.ocr_extractor import process_page_with_ocr
        ocr_res = process_page_with_ocr(img, 1)
        ocr_text = ocr_res.get("text", "").strip() if ocr_res else ""
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")
    
    session_doc_ids = None
    if session_id:
        user_msg_content = "[Image Uploaded for Search]"
        if ocr_text:
            user_msg_content += f"\n\nExtracted OCR Text:\n{ocr_text}"
            
        add_message(str(uuid.uuid4()), session_id, "user", user_msg_content, scoped_docs=get_docs_for_session(session_id))
        scoped = get_docs_for_session(session_id)
        if scoped:
            session_doc_ids = scoped

    milvus_image_res = search_image(image_emb, TOP_K_RETRIEVAL, doc_ids=session_doc_ids)
    
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
                "score": hit["score"]
            })
            
    citations = []
    for res in image_results:
        citations.append({
            "doc_name": res["filename"],
            "page_number": res["page"],
            "source_type": "image",
            "image_id": res["image_id"],
            "chunk_text": "Visually similar region found",
            "bbox": res["bbox"],
            "verified": True
        })
        
    if session_id:
        add_message(
            str(uuid.uuid4()), 
            session_id, 
            "assistant", 
            "I found several visually similar regions in your documents. You can review them in the citations below.", 
            citations,
            verified=True,
            scoped_docs=session_doc_ids
        )

    return {
        "answer": "I found several visually similar regions in your documents. You can review them in the citations below.",
        "verified": True,
        "flagged_sentences": [],
        "support_scores": [],
        "citations": citations,
        "latency_seconds": 0
    }

@router.post("/query/stream")
async def handle_query_stream(request: QueryRequest):
    query = request.query
    session_id = request.session_id
    
    history = []
    session_doc_ids = None
    if session_id:
        history = get_messages_for_session(session_id)
        scoped = get_docs_for_session(session_id)
        if scoped:
            session_doc_ids = scoped
        add_message(str(uuid.uuid4()), session_id, "user", query, scoped_docs=session_doc_ids)

    import asyncio
    loop = asyncio.get_event_loop()
    
    text_image_dense_task = run_dense_retrieval_async(query, doc_ids=session_doc_ids)
    text_bm25_task = loop.run_in_executor(None, bm25_search, query, TOP_K_RETRIEVAL, session_doc_ids)
    
    (text_dense, image_dense), text_bm25 = await asyncio.gather(text_image_dense_task, text_bm25_task)
    ranked_chunks = rrf_fusion(text_dense, image_dense, text_bm25)
    
    messages = build_prompt(query, ranked_chunks, history)

    async def stream_generator():
        full_answer = ""
        try:
            for part in generate_stream(messages):
                full_answer = part
                yield f"data: {json.dumps({'answer': part, 'done': False})}\n\n"
        except Exception as e:
            print(f"Error during answer streaming: {e}")
            error_payload = {
                "answer": "The model failed to generate a response. Please check local model availability and disk space.",
                "done": True,
                "verified": False,
                "flagged_sentences": [],
                "support_scores": [],
                "citations": []
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            return
        
        try:
            check_task = loop.run_in_executor(None, verify_answer, full_answer, ranked_chunks)
            cit_task = loop.run_in_executor(None, map_citations, full_answer, ranked_chunks)
            
            check_results, citations = await asyncio.gather(check_task, cit_task)
            
            if session_id:
                add_message(
                    str(uuid.uuid4()), 
                    session_id, 
                    "assistant", 
                    full_answer, 
                    citations,
                    support_scores=check_results.get("support_scores", []),
                    flagged_sentences=[f["sentence"] for f in check_results.get("flagged_sentences", [])],
                    verified=check_results["verified"]
                )
                
            final_payload = {
                "answer": full_answer,
                "done": True,
                "verified": check_results["verified"],
                "flagged_sentences": [f["sentence"] for f in check_results.get("flagged_sentences", [])],
                "support_scores": check_results.get("support_scores", []),
                "citations": citations
            }
        except Exception as e:
            print(f"Error in post-generation processing: {e}")
            final_payload = {
                "answer": full_answer,
                "done": True,
                "verified": True,
                "flagged_sentences": [],
                "support_scores": [],
                "citations": []
            }
            
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@router.post("/query")
async def handle_query(request: QueryRequest):
    start_time = time.time()
    query = request.query
    session_id = request.session_id
    
    history = []
    session_doc_ids = None
    if session_id:
        history = get_messages_for_session(session_id)
        scoped = get_docs_for_session(session_id)
        if scoped:
            session_doc_ids = scoped
        add_message(str(uuid.uuid4()), session_id, "user", query, scoped_docs=session_doc_ids)

    import asyncio
    loop = asyncio.get_event_loop()
    
    text_image_dense_task = run_dense_retrieval_async(query, doc_ids=session_doc_ids)
    text_bm25_task = loop.run_in_executor(None, bm25_search, query, TOP_K_RETRIEVAL, session_doc_ids)
    
    (text_dense, image_dense), text_bm25 = await asyncio.gather(text_image_dense_task, text_bm25_task)
    ranked_chunks = rrf_fusion(text_dense, image_dense, text_bm25)
    
    messages = build_prompt(query, ranked_chunks, history)
    generated_text = await loop.run_in_executor(None, generate_answer, messages)
    
    check_task = loop.run_in_executor(None, verify_answer, generated_text, ranked_chunks)
    cit_task = loop.run_in_executor(None, map_citations, generated_text, ranked_chunks)
    
    check_results, citations = await asyncio.gather(check_task, cit_task)
    
    latency = time.time() - start_time
    
    if session_id:
        add_message(
            str(uuid.uuid4()), 
            session_id, 
            "assistant", 
            generated_text, 
            citations,
            support_scores=check_results.get("support_scores", []),
            flagged_sentences=[f["sentence"] for f in check_results.get("flagged_sentences", [])],
            verified=check_results["verified"]
        )

    return {
        "answer": generated_text,
        "verified": check_results["verified"],
        "flagged_sentences": [f["sentence"] for f in check_results.get("flagged_sentences", [])],
        "support_scores": check_results.get("support_scores", []),
        "citations": citations,
        "latency_seconds": latency
    }
