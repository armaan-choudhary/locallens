import os
import time
import uuid
import shutil
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from PIL import Image

from ingestion.preprocessor import process_path
from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_images
from storage.postgres_store import (
    insert_document, bulk_insert_text_chunks, bulk_insert_image_regions, 
    get_all_documents, delete_document_data, init_postgres,
    create_session, get_all_sessions, get_messages_for_session, 
    add_message, delete_session,
    add_doc_to_session, remove_doc_from_session, get_docs_for_session,
    get_image_by_milvus_id
)
from storage.milvus_store import (
    insert_text_vectors, insert_image_vectors, init_milvus, delete_by_doc_id,
    search_image
)
from retrieval.dense_retriever import run_dense_retrieval_async
from retrieval.bm25_retriever import search as bm25_search, mark_dirty
from retrieval.rrf_fusion import rrf_fusion
from generation.prompt_builder import build_prompt
from generation.llm_runner import generate as generate_answer, generate_stream
from generation.hallucination_checker import verify_answer
from citation.citation_mapper import map_citations
from config import TOP_K_RETRIEVAL

app = FastAPI(title="LocalLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:7860"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}

class QueryRequest(BaseModel):
    query: str
    session_id: str = None

@app.on_event("startup")
async def startup_event():
    init_postgres()
    init_milvus()

@app.get("/documents")
async def get_documents():
    docs = get_all_documents()
    formatted = []
    for d in docs:
        formatted.append({
            "doc_id": d["doc_id"],
            "filename": d["filename"],
            "page_count": d["page_count"],
            "chunk_count": d["chunk_count"],
            "ingested_at": d.get("ingested_at", "").isoformat() if hasattr(d.get("ingested_at"), "isoformat") else str(d.get("ingested_at", ""))
        })
    return formatted

@app.get("/documents/{doc_id}/details")
async def get_doc_details(doc_id: str):
    from storage.postgres_store import get_pool
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM documents WHERE doc_id = %s", (doc_id,))
            doc = cur.fetchone()
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            cur.execute("SELECT image_id, page_number, bbox_x1, bbox_y1, bbox_x2, bbox_y2 FROM image_regions WHERE doc_id = %s", (doc_id,))
            images = cur.fetchall()
            
            cur.execute("SELECT chunk_id, page_number, text, source FROM text_chunks WHERE doc_id = %s ORDER BY chunk_index ASC LIMIT 10", (doc_id,))
            chunks = cur.fetchall()
            
            return {
                "metadata": {
                    "doc_id": doc["doc_id"],
                    "filename": doc["filename"],
                    "page_count": doc["page_count"],
                    "ingested_at": doc["ingested_at"].isoformat() if hasattr(doc["ingested_at"], "isoformat") else str(doc["ingested_at"])
                },
                "images": images,
                "chunks": chunks
            }
    finally:
        pool.putconn(conn)

@app.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str):
    delete_document_data(doc_id)
    delete_by_doc_id(doc_id)
    mark_dirty()
    return {"success": True}

@app.get("/sessions")
async def list_sessions():
    return get_all_sessions()

@app.post("/sessions")
async def start_session(title: str = "New Chat"):
    session_id = str(uuid.uuid4())
    create_session(session_id, title)
    return {"session_id": session_id}

@app.get("/sessions/{session_id}/messages")
async def list_messages(session_id: str):
    return get_messages_for_session(session_id)

@app.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"success": True}

@app.get("/sessions/{session_id}/documents")
async def list_session_docs(session_id: str):
    doc_ids = get_docs_for_session(session_id)
    return {"doc_ids": doc_ids}

@app.post("/sessions/{session_id}/documents/{doc_id}")
async def add_session_doc(session_id: str, doc_id: str):
    add_doc_to_session(session_id, doc_id)
    return {"success": True}

@app.post("/sessions/{session_id}/documents/bulk/add")
async def add_session_docs_bulk(session_id: str, doc_ids: List[str]):
    for doc_id in doc_ids:
        add_doc_to_session(session_id, doc_id)
    return {"success": True}

@app.delete("/sessions/{session_id}/documents/{doc_id}")
async def remove_session_doc(session_id: str, doc_id: str):
    remove_doc_from_session(session_id, doc_id)
    return {"success": True}

@app.post("/sessions/{session_id}/documents/bulk/remove")
async def remove_session_docs_bulk(session_id: str, doc_ids: List[str]):
    for doc_id in doc_ids:
        remove_doc_from_session(session_id, doc_id)
    return {"success": True}

@app.delete("/sessions/{session_id}/documents/bulk/clear")
async def clear_session_docs(session_id: str):
    current_docs = get_docs_for_session(session_id)
    for doc_id in current_docs:
        remove_doc_from_session(session_id, doc_id)
    return {"success": True}

@app.get("/api/images/{image_id}")
async def get_image_file(image_id: str):
    img_path = os.path.join("storage", "images", f"{image_id}.png")
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

@app.post("/api/search/image")
async def search_by_image(file: UploadFile = File(...), session_id: str = None):
    # Vector search for visual similarity within session context
    try:
        img = Image.open(file.file).convert("RGB")
        image_emb = embed_images([img])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")
    
    session_doc_ids = None
    if session_id:
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
            verified=True
        )

    return {
        "answer": "I found several visually similar regions in your documents. You can review them in the citations below.",
        "verified": True,
        "flagged_sentences": [],
        "support_scores": [],
        "citations": citations,
        "latency_seconds": 0
    }

@app.get("/ingest/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

def process_ingestion(job_id: str, file_paths: List[str]):
    # Asynchronous pipeline: text/image extraction, embedding, and dual-store indexing
    for i, filepath in enumerate(file_paths):
        filename = os.path.basename(filepath)
        jobs[job_id]["filename"] = filename
        jobs[job_id]["log_lines"].append(f"Ingesting: {filename}")
        
        try:
            jobs[job_id]["stage"] = "extracting"
            documents, all_text_chunks, all_image_crops = process_path(filepath)
            
            doc_id = documents[0]["doc_id"]
            jobs[job_id]["total_pages"] = documents[0]["page_count"]
            
            insert_document(doc_id, filename, filepath, documents[0]["page_count"])
            
            if all_text_chunks:
                jobs[job_id]["stage"] = "embedding"
                text_texts = [c["text"] for c in all_text_chunks]
                text_embs = embed_texts(text_texts)
                
                jobs[job_id]["stage"] = "indexing"
                milvus_ids = insert_text_vectors(text_embs, [doc_id]*len(all_text_chunks))
                
                chunks_data = []
                for j, chunk in enumerate(all_text_chunks):
                    m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                    chunks_data.append((
                        chunk["chunk_id"], doc_id, chunk["page_number"],
                        chunk["chunk_index"], chunk["char_start"], chunk["char_end"],
                        chunk["text"], chunk["source"], m_id
                    ))
                bulk_insert_text_chunks(chunks_data)
                mark_dirty()

                if all_image_crops:
                    jobs[job_id]["stage"] = "embedding_images"
                    img_objs = [c["image"] for c in all_image_crops]
                    img_embs = embed_images(img_objs)
                    milvus_ids = insert_image_vectors(img_embs, [doc_id]*len(all_image_crops))
                    
                    regions_data = []
                    for j, crop in enumerate(all_image_crops):
                        img_id = crop["image_id"]
                        m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                        bbox = crop["bbox"]
                        
                        img_path = os.path.join("storage", "images", f"{img_id}.png")
                        crop["image"].save(img_path)
                        
                        regions_data.append((
                            img_id, doc_id, crop["page_number"],
                            crop["image_index"], bbox[0], bbox[1], bbox[2], bbox[3], m_id, None, img_path
                        ))
                    bulk_insert_image_regions(regions_data)
            
            jobs[job_id]["log_lines"].append(f"✓ {filename} complete.")
            
        except Exception as e:
            jobs[job_id]["stage"] = "error"
            jobs[job_id]["log_lines"].append(f"✗ Failed: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    jobs[job_id]["stage"] = "done"

@app.post("/ingest")
async def ingest_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "filename": "Pending",
        "current_page": 0,
        "total_pages": 0,
        "stage": "starting",
        "log_lines": []
    }
    
    temp_dir = "/tmp/locallens_ingest"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_paths = []
    for file in files:
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(temp_path)
    
    background_tasks.add_task(process_ingestion, job_id, file_paths)
    return {"job_id": job_id}

@app.post("/query/stream")
async def handle_query_stream(request: QueryRequest):
    # Streamed RAG: hybrid retrieval followed by asynchronous verification
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
        for part in generate_stream(messages):
            full_answer = part
            yield f"data: {json.dumps({'answer': part, 'done': False})}\n\n"
        
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
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/query")
async def handle_query(request: QueryRequest):
    # Synchronous RAG workflow with parallel retrieval and post-processing
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
