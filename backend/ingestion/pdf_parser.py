import os
from PyPDF2 import PdfReader

def extract_text_from_page(page, page_num: int) -> dict:
    """
    Extract text from a single PDF page with basic layout preservation.
    """
    text_blocks = []
    
    def visitor_body(text, cm, tm, fontDict, fontSize):
        if text.strip():
            text_blocks.append({"text": text, "x": tm[4], "y": -tm[5]})

    try:
        page.extract_text(visitor_text=visitor_body)
    except Exception as e:
        print(f"Extraction failed on page {page_num}: {e}")
    
    if not text_blocks:
        return {"page": page_num, "text": ""}

    COLUMN_WIDTH_APPROX = 150
    text_blocks.sort(key=lambda b: (b["x"] // COLUMN_WIDTH_APPROX, b["y"]))
    
    page_text = "".join([b["text"] for b in text_blocks]).replace("\n", " ").strip()
    return {"page": page_num, "text": page_text}

def extract_text_from_pdf(filepath: str) -> list[dict]:
    """
    Extract text from all pages of a PDF file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    reader = PdfReader(filepath)
    return [extract_text_from_page(reader.pages[i], i + 1) for i in range(len(reader.pages))]
