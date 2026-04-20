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

@app.get("/api/images/{image_id}")
async def get_image_file(image_id: str):
    # Determine the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(current_dir, "storage", "images", f"{image_id}.png")
    if not os.path.exists(img_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
