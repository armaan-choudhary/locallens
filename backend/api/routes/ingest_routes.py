import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from api.services.ingestion_service import process_ingestion, jobs
from config import INGEST_TEMP_DIR

router = APIRouter()

@router.get("/ingest/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@router.post("/ingest")
async def ingest_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "filename": "Pending",
        "current_page": 0,
        "total_pages": 0,
        "stage": "starting",
        "log_lines": []
    }
    
    os.makedirs(INGEST_TEMP_DIR, exist_ok=True)
    
    file_paths = []
    for file in files:
        temp_path = os.path.join(INGEST_TEMP_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(temp_path)
    
    background_tasks.add_task(process_ingestion, job_id, file_paths)
    return {"job_id": job_id}
