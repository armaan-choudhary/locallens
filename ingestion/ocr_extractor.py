import pytesseract
from pytesseract import Output
from PIL import Image

def process_page_with_ocr(image: Image.Image, page_num: int) -> dict:
    """
    Run Tesseract OCR on a given page image.
    Extracts raw text and word-level bounding boxes.
    Returns:
        {
            "page": int,
            "text": str,
            "word_boxes": [{"word": str, "bbox": [x, y, w, h]}]
        }
    """
    try:
        # Run text extraction
        text = pytesseract.image_to_string(image)
        
        # Run data extraction for bounding boxes
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
        
        word_boxes = []
        for i in range(len(data['text'])):
            word = data['text'][i].strip()
            if word: # Filter out empty words
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                word_boxes.append({
                    "word": word,
                    "bbox": [x, y, w, h]
                })

        return {
            "page": page_num,
            "text": text.strip(),
            "word_boxes": word_boxes
        }
    except Exception as e:
        print(f"OCR Exception on page {page_num}: {e}")
        return {
            "page": page_num,
            "text": "",
            "word_boxes": []
        }
