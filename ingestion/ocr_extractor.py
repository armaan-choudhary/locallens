import pytesseract
from pytesseract import Output
from PIL import Image

def process_page_with_ocr(image: Image.Image, page_num: int) -> dict:
    """
    Perform OCR on a page image to extract text and word-level bounding boxes.
    """
    try:
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
        
        word_boxes = []
        for i in range(len(data['text'])):
            word = data['text'][i].strip()
            if word:
                word_boxes.append({
                    "word": word,
                    "bbox": [data['left'][i], data['top'][i], data['width'][i], data['height'][i]]
                })

        return {
            "page": page_num,
            "text": text.strip(),
            "word_boxes": word_boxes
        }
    except Exception as e:
        print(f"OCR failed on page {page_num}: {e}")
        return {"page": page_num, "text": "", "word_boxes": []}
