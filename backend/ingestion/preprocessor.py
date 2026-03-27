import os
import uuid
import concurrent.futures
from typing import Tuple, List, Dict
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

from config import CHUNK_SIZE, CHUNK_OVERLAP
from ingestion.pdf_parser import extract_text_from_page
from ingestion.image_extractor import process_page_images
from ingestion.ocr_extractor import process_page_with_ocr

def process_pdf(filepath: str, doc_id: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a PDF file to extract text chunks and image regions.
    """
    try:
        reader = PdfReader(filepath)
        num_pages = len(reader.pages)
    except Exception as e:
        print(f"Failed to read PDF {filepath}: {e}")
        return [], []

    all_text_pages = {}
    all_image_crops = []
    BATCH_SIZE = 10 
    
    for batch_start in range(1, num_pages + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE - 1, num_pages)
        
        try:
            batch_images = convert_from_path(
                filepath, 
                first_page=batch_start, 
                last_page=batch_end, 
                dpi=150, 
                thread_count=4
            )
        except Exception as e:
            print(f"Failed to render pages {batch_start}-{batch_end}: {e}")
            batch_images = [None] * (batch_end - batch_start + 1)

        page_tasks = []
        for i, page_num in enumerate(range(batch_start, batch_end + 1)):
            page_img = batch_images[i]
            page_obj = reader.pages[page_num - 1]
            text_info = extract_text_from_page(page_obj, page_num)
            page_tasks.append((text_info, page_img, page_num))

        def page_worker(task):
            t_info, p_img, p_num = task
            text = t_info["text"]
            source = "PyPDF2"
            
            if not text.strip() and p_img:
                ocr_result = process_page_with_ocr(p_img, p_num)
                text = ocr_result["text"]
                source = "tesseract"
            
            img_crops = process_page_images(p_img, p_num) if p_img else []
            return p_num, text, source, img_crops

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as batch_executor:
            results = list(batch_executor.map(page_worker, page_tasks))
        
        for p_num, text, source, img_crops in results:
            all_text_pages[p_num] = {"text": text, "source": source}
            all_image_crops.extend(img_crops)
        
        del batch_images

    text_chunks = []
    chunk_index = 0
    for page_num in sorted(all_text_pages.keys()):
        page_info = all_text_pages[page_num]
        full_text = page_info["text"]
        source = page_info["source"]
        
        if not full_text.strip():
            continue
            
        char_start = 0
        while char_start < len(full_text):
            char_end = min(char_start + CHUNK_SIZE, len(full_text))
            text_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "page_number": page_num,
                "chunk_index": chunk_index,
                "char_start": char_start,
                "char_end": char_end,
                "text": full_text[char_start:char_end],
                "source": source
            })
            chunk_index += 1
            char_start += (CHUNK_SIZE - CHUNK_OVERLAP)

    tagged_images = []
    for i, crop in enumerate(all_image_crops):
        tagged_images.append({
            "image_id": str(uuid.uuid4()),
            "doc_id": doc_id,
            "page_number": crop["page"],
            "image_index": i,
            "bbox": crop["bbox"],
            "image": crop["image"]
        })

    return text_chunks, tagged_images

def process_image(filepath: str, doc_id: str) -> Tuple[List[Dict], List[Dict]]:
    try:
        img = Image.open(filepath).convert("RGB")
    except Exception as e:
        print(f"Failed to read Image {filepath}: {e}")
        return [], []
        
    page_num = 1
    ocr_result = process_page_with_ocr(img, page_num)
    text = ocr_result["text"]
    source = "tesseract"
    
    text_chunks = []
    if text.strip():
        char_start = 0
        chunk_index = 0
        while char_start < len(text):
            char_end = min(char_start + CHUNK_SIZE, len(text))
            text_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "page_number": page_num,
                "chunk_index": chunk_index,
                "char_start": char_start,
                "char_end": char_end,
                "text": text[char_start:char_end],
                "source": source
            })
            chunk_index += 1
            char_start += (CHUNK_SIZE - CHUNK_OVERLAP)
            
    tagged_images = [{
        "image_id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "page_number": page_num,
        "image_index": 0,
        "bbox": [0, 0, img.width, img.height],
        "image": img
    }]
    
    return text_chunks, tagged_images

def process_path(path: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Process a PDF file or a directory containing PDF files and Images.
    """
    documents, all_text_chunks, all_image_crops = [], [], []
    files_to_process = []
    
    valid_exts = {".pdf", ".png", ".jpg", ".jpeg"}
    
    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in valid_exts:
        files_to_process.append(path)
    elif os.path.isdir(path):
        files_to_process = [
            os.path.join(path, f) for f in os.listdir(path) 
            if os.path.splitext(f)[1].lower() in valid_exts
        ]
                
    for filepath in files_to_process:
        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            text_chunks, tagged_images = process_pdf(filepath, doc_id)
        else:
            text_chunks, tagged_images = process_image(filepath, doc_id)
        
        pages = set([c["page_number"] for c in text_chunks] + [img["page_number"] for img in tagged_images])
        
        documents.append({
            "doc_id": doc_id,
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "page_count": max(pages) if pages else 1
        })
        all_text_chunks.extend(text_chunks)
        all_image_crops.extend(tagged_images)
        
    return documents, all_text_chunks, all_image_crops
