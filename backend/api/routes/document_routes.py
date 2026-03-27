import os
from typing import List
from fastapi import APIRouter, HTTPException
from storage.postgres_store import get_all_documents, delete_document_data
from storage.milvus_store import delete_by_doc_id
from retrieval.bm25_retriever import mark_dirty
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/documents")
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

@router.get("/documents/{doc_id}/details")
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

@router.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str):
    delete_document_data(doc_id)
    delete_by_doc_id(doc_id)
    mark_dirty()
    return {"success": True}
