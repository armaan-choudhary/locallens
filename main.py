import os
import time
import uuid
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion.preprocessor import process_path
from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_images
from storage.postgres_store import (
    insert_document, insert_text_chunk, insert_image_region, 
    get_all_documents, delete_document_data, init_postgres
)
from storage.milvus_store import (
    insert_text_vectors, insert_image_vectors, init_milvus, delete_by_doc_id
)
from retrieval.dense_retriever import run_dense_retrieval
from retrieval.bm25_retriever import search as bm25_search, mark_dirty
from retrieval.rrf_fusion import rrf_fusion
from generation.prompt_builder import build_prompt
from generation.llm_runner import generate as generate_answer
from generation.hallucination_checker import verify_answer
from citation.citation_mapper import map_citations
from config import TOP_K_RETRIEVAL

app = FastAPI(title="LocalLens API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:7860"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global job status store
jobs = {}

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    print("Initialising LocalLens Metadata...")
    init_postgres()
    print("Initialising LocalLens Vector Store...")
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

@app.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str):
    delete_document_data(doc_id)
    delete_by_doc_id(doc_id)
    return {"success": True}

@app.get("/ingest/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

def process_ingestion(job_id: str, file_paths: List[str]):
    for i, filepath in enumerate(file_paths):
        filename = os.path.basename(filepath)
        jobs[job_id]["filename"] = filename
        jobs[job_id]["log_lines"].append(f"Ingesting: {filename}")
        
        try:
            # 1. Extraction
            jobs[job_id]["stage"] = "extracting"
            documents, all_text_chunks, all_image_crops = process_path(filepath)
            
            doc_id = documents[0]["doc_id"]
            jobs[job_id]["total_pages"] = documents[0]["page_count"]
            
            # 2. Metadata storage
            insert_document(doc_id, filename, filepath, documents[0]["page_count"])
            
            # 3. Text pipeline
            if all_text_chunks:
                jobs[job_id]["stage"] = "embedding"
                text_texts = [c["text"] for c in all_text_chunks]
                text_embs = embed_texts(text_texts)
                
                jobs[job_id]["stage"] = "indexing"
                milvus_ids = insert_text_vectors(text_embs, [doc_id]*len(all_text_chunks))
                
                for j, chunk in enumerate(all_text_chunks):
                    m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                    insert_text_chunk(
                        chunk["chunk_id"], doc_id, chunk["page_number"],
                        chunk["chunk_index"], chunk["char_start"], chunk["char_end"],
                        chunk["text"], chunk["source"], m_id
                    )
                mark_dirty()

            # 4. Image pipeline
            if all_image_crops:
                img_objs = [c["image"] for c in all_image_crops]
                img_embs = embed_images(img_objs)
                milvus_ids = insert_image_vectors(img_embs, [doc_id]*len(all_image_crops))
                
                for j, crop in enumerate(all_image_crops):
                    nearby_chunk_id = None
                    m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                    insert_image_region(
                        crop["image_id"], doc_id, crop["page_number"],
                        crop["image_index"], crop["bbox"], m_id, nearby_chunk_id
                    )
            
            jobs[job_id]["log_lines"].append(f"✓ {filename} complete.")
            
        except Exception as e:
            jobs[job_id]["stage"] = "error"
            jobs[job_id]["log_lines"].append(f"✗ Failed: {str(e)}")
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

@app.post("/query")
async def handle_query(request: QueryRequest):
    start_time = time.time()
    query = request.query
    
    # Retrieval
    text_dense, image_dense = run_dense_retrieval(query)
    text_bm25 = bm25_search(query, TOP_K_RETRIEVAL)
    ranked_chunks = rrf_fusion(text_dense, image_dense, text_bm25)
    
    # Generation
    prompt = build_prompt(query, ranked_chunks)
    generated_text = generate_answer(prompt)
    check_results = verify_answer(generated_text, ranked_chunks)
    
    # Citations
    citations = map_citations(generated_text, ranked_chunks)
    
    return {
        "answer": generated_text,
        "verified": check_results["verified"],
        "flagged_sentences": check_results.get("flagged_sentences", []),
        "citations": citations,
        "latency_seconds": time.time() - start_time
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
