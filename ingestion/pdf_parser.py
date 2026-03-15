import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(filepath: str) -> list[dict]:
    """
    Extracts text from a PDF file page by page.
    Attempts to handle multi-column layouts using a basic bounding-box heuristic.
    Returns: [{"page": 1, "text": "Raw text..."}, ...]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    reader = PdfReader(filepath)
    results = []

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        
        text_blocks = []
        
        def visitor_body(text, cm, tm, fontDict, fontSize):
            if text.strip():
                # tm is the text matrix. tm[4] is X, tm[5] is Y.
                # In PDF, Y usually starts from bottom, so we may want to invert it for top-to-bottom sorting.
                x = tm[4]
                y = tm[5]
                text_blocks.append({"text": text, "x": x, "y": -y})

        # extract_text will trigger the visitor for each text snippet
        try:
            page.extract_text(visitor_text=visitor_body)
        except Exception as e:
            # If extraction fails for a page, handle gracefully
            print(f"Warning: Failed to extract text from page {page_num + 1} of {filepath}: {e}")
            pass
        
        if not text_blocks:
            # Maybe scanned page, return empty string for OCR
            results.append({"page": page_num + 1, "text": ""})
            continue

        # To handle columns, we want to group by X somewhat, or sort by X (columns left to right),
        # then by Y (top to bottom).
        # A simple sort: x // column_width, then y
        # We can approximate the page into 2 or 3 vertical buckets.
        # But a more generic way is to sort by x and y.
        # To avoid strictly sorting by x and messing up lines in the same column:
        # We define a column threshold (e.g., 50 units). 
        # But for simplicity, we can just sort by a rounded X (say, groups of 100), then Y.
        
        # Heuristic: sort top-to-bottom (y), left-to-right (x) with a small allowance on y
        # Wait, the prompt says: "sort text blocks top-to-bottom, left-to-right per column"
        # Standard approach for columns: sort by (X // column_width, Y).
        # Let's use a bucket size for X of roughly 250 (half a standard ~500pt page) or use round.
        
        # Let's implement a rounded X approach for columns.
        COLUMN_WIDTH_APPROX = 150
        
        text_blocks.sort(key=lambda b: (b["x"] // COLUMN_WIDTH_APPROX, b["y"]))
        
        # Join text
        page_text = "".join([b["text"] for b in text_blocks])
        
        # Basic cleanup
        page_text = page_text.replace("\n", " ").strip()
        
        results.append({
            "page": page_num + 1,
            "text": page_text
        })

    return results
