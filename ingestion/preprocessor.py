import os
import uuid
from typing import Tuple, List, Dict
from PIL import Image

from config import CHUNK_SIZE, CHUNK_OVERLAP
from ingestion.pdf_parser import extract_text_from_pdf
from ingestion.image_extractor import extract_images_from_pdf
from ingestion.ocr_extractor import process_page_with_ocr

def process_pdf(filepath: str, doc_id: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a single PDF file, extract text chunks and images.
    Returns:
        (text_chunks, image_crops)
    """
    print(f"Processing document: {filepath}")
    
    # 1. Image extraction (renders all pages, crops images)
    try:
        image_crops, full_renders = extract_images_from_pdf(filepath)
    except Exception as e:
        print(f"Failed to process images for {filepath}: {e}")
        return [], []

    # Map full page renders for OCR
    full_renders_dict = {render["page"]: render["image"] for render in full_renders}

    # 2. Text Extraction via PyPDF2
    try:
        pypdf_results = extract_text_from_pdf(filepath)
    except Exception as e:
        print(f"Failed to parse text from {filepath}: {e}")
        return [], []

    text_pages = {}
    
    # 3. Handle empty pages with Tesseract OCR fallback
    for p_info in pypdf_results:
        page_num = p_info["page"]
        text = p_info["text"]
        
        if not text.strip() and page_num in full_renders_dict:
            # Fallback to OCR
            print(f"Page {page_num} seems empty, falling back to OCR.")
            ocr_result = process_page_with_ocr(full_renders_dict[page_num], page_num)
            text_pages[page_num] = {
                "text": ocr_result["text"],
                "source": "tesseract"
            }
        else:
            text_pages[page_num] = {
                "text": text,
                "source": "PyPDF2"
            }

    # 4. Chunking
    text_chunks = []
    chunk_index = 0
    
    for page_num in sorted(text_pages.keys()):
        page_info = text_pages[page_num]
        full_text = page_info["text"]
        source = page_info["source"]
        
        if not full_text.strip():
            continue
            
        char_start = 0
        while char_start < len(full_text):
            char_end = min(char_start + CHUNK_SIZE, len(full_text))
            
            chunk_text = full_text[char_start:char_end]
            
            # Record chunk
            text_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "page_number": page_num,
                "chunk_index": chunk_index,
                "char_start": char_start,
                "char_end": char_end,
                "text": chunk_text,
                "source": source
            })
            
            chunk_index += 1
            char_start += (CHUNK_SIZE - CHUNK_OVERLAP)

    # 5. Tag images
    tagged_images = []
    for i, crop in enumerate(image_crops):
        tagged_images.append({
            "image_id": str(uuid.uuid4()),
            "doc_id": doc_id,
            "page_number": crop["page"],
            "image_index": i,
            "bbox": crop["bbox"],
            "image": crop["image"]
        })

    return text_chunks, tagged_images

def process_path(path: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Process a single PDF or a directory of PDFs.
    Returns:
        (documents, all_text_chunks, all_image_crops)
    """
    documents = []
    all_text_chunks = []
    all_image_crops = []
    
    files_to_process = []
    
    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        files_to_process.append(path)
    elif os.path.isdir(path):
        for f in os.listdir(path):
            if f.lower().endswith(".pdf"):
                files_to_process.append(os.path.join(path, f))
                
    for filepath in files_to_process:
        doc_id = str(uuid.uuid4())
        filename = os.path.basename(filepath)
        
        text_chunks, tagged_images = process_pdf(filepath, doc_id)
        
        # Determine page count heuristically
        pages = set([c["page_number"] for c in text_chunks] + [img["page_number"] for img in tagged_images])
        page_count = max(pages) if pages else 0
        
        documents.append({
            "doc_id": doc_id,
            "filename": filename,
            "filepath": filepath,
            "page_count": page_count
        })
        
        all_text_chunks.extend(text_chunks)
        all_image_crops.extend(tagged_images)
        
    return documents, all_text_chunks, all_image_crops
