import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from storage.postgres_store import init_postgres
from storage.milvus_store import init_milvus
from api.routes import document_routes, session_routes, query_routes, ingest_routes
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_postgres()
    init_milvus()
    yield

app = FastAPI(title="LocalLens API", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:7860"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(document_routes.router, tags=["Documents"])
app.include_router(session_routes.router, tags=["Sessions"])
app.include_router(query_routes.router, tags=["Queries"])
app.include_router(ingest_routes.router, tags=["Ingestion"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Serve internal image files
from fastapi.responses import FileResponse
import os

@app.get("/images/{image_id}")
async def get_image_file(image_id: str):
    # Determine the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(current_dir, "storage", "images", f"{image_id}.png")
    if not os.path.exists(img_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

@app.get("/documents/{doc_id}/pdf")
async def get_document_pdf(doc_id: str):
    """Serve the original PDF file for in-browser viewing."""
    from fastapi import HTTPException
    from storage.postgres_store import get_pool
    from psycopg2.extras import RealDictCursor
    
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT filepath, filename FROM documents WHERE doc_id = %s", (doc_id,))
            doc = cur.fetchone()
    finally:
        pool.putconn(conn)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    filepath = doc["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="PDF file no longer available on disk")
    
    return FileResponse(filepath, media_type="application/pdf", filename=doc["filename"])

@app.get("/documents/{doc_id}/page/{page_number}")
async def get_document_page(doc_id: str, page_number: int):
    """Render a specific PDF page as a PNG image.
    Falls back to compositing stored image crops when the source PDF is unavailable."""
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    from storage.postgres_store import get_pool
    from psycopg2.extras import RealDictCursor
    from PIL import Image as PILImage
    import io
    
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT filepath FROM documents WHERE doc_id = %s", (doc_id,))
            doc = cur.fetchone()
    finally:
        pool.putconn(conn)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    filepath = doc["filepath"]
    
    # Primary: render from source PDF
    if os.path.exists(filepath):
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(filepath, first_page=page_number, last_page=page_number, dpi=200)
            if not pages:
                raise HTTPException(status_code=404, detail="Page not found")
            
            buf = io.BytesIO()
            pages[0].save(buf, format="PNG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render page: {str(e)}")
    
    # Fallback: composite stored image crops for this page
    from config import STORAGE_IMAGES_DIR
    
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT image_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2 
                   FROM image_regions 
                   WHERE doc_id = %s AND page_number = %s 
                   ORDER BY bbox_y1 ASC, bbox_x1 ASC""",
                (doc_id, page_number)
            )
            regions = cur.fetchall()
            
            # Also get text chunks for this page to show text content
            cur.execute(
                """SELECT text FROM text_chunks 
                   WHERE doc_id = %s AND page_number = %s 
                   ORDER BY chunk_index ASC""",
                (doc_id, page_number)
            )
            chunks = cur.fetchall()
    finally:
        pool.putconn(conn)
    
    if not regions and not chunks:
        raise HTTPException(status_code=404, detail="No content found for this page. Re-ingest the document to enable source viewing.")
    
    # Build a composite image from stored crops
    if regions:
        # Find the bounding extent of all regions
        max_x = max(r["bbox_x2"] for r in regions)
        max_y = max(r["bbox_y2"] for r in regions)
        canvas_w = max(max_x + 40, 1200)
        canvas_h = max(max_y + 40, 1600)
        
        canvas = PILImage.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        
        for region in regions:
            img_path = os.path.join(STORAGE_IMAGES_DIR, f"{region['image_id']}.png")
            if os.path.exists(img_path):
                try:
                    crop_img = PILImage.open(img_path)
                    canvas.paste(crop_img, (region["bbox_x1"], region["bbox_y1"]))
                except Exception:
                    pass
        
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    
    # Text-only fallback: render text chunks as an image
    try:
        from PIL import ImageDraw, ImageFont
        canvas = PILImage.new("RGB", (1200, 1600), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        except Exception:
            font = ImageFont.load_default()
        
        y_offset = 40
        draw.text((40, y_offset), f"Page {page_number}", fill=(100, 100, 100), font=font)
        y_offset += 40
        
        for chunk in chunks:
            text = chunk["text"]
            # Word wrap at ~90 chars
            words = text.split()
            line = ""
            for word in words:
                if len(line) + len(word) + 1 > 90:
                    draw.text((40, y_offset), line, fill=(30, 30, 30), font=font)
                    y_offset += 20
                    line = word
                else:
                    line = f"{line} {word}".strip()
            if line:
                draw.text((40, y_offset), line, fill=(30, 30, 30), font=font)
                y_offset += 30
        
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render fallback: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
