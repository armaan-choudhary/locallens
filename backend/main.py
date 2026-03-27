import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from storage.postgres_store import init_postgres
from storage.milvus_store import init_milvus
from api.routes import document_routes, session_routes, query_routes, ingest_routes

app = FastAPI(title="LocalLens API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:7860"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_postgres()
    init_milvus()

# Include Routers
app.include_router(document_routes.router, tags=["Documents"])
app.include_router(session_routes.router, tags=["Sessions"])
app.include_router(query_routes.router, tags=["Queries"])
app.include_router(ingest_routes.router, tags=["Ingestion"])

# Serve internal image files
from fastapi.responses import FileResponse
import os

@app.get("/api/images/{image_id}")
async def get_image_file(image_id: str):
    img_path = os.path.join("storage", "images", f"{image_id}.png")
    if not os.path.exists(img_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
