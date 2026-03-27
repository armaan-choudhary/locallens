import os
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path

def process_page_images(page_img: Image.Image, page_num: int) -> list[dict]:
    """
    Detect and crop non-text regions (figures, diagrams) from a page image.
    """
    cv_img = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cropped_images = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 100 and h > 100:
            cropped_images.append({
                "page": page_num,
                "image": page_img.crop((x, y, x + w, y + h)),
                "bbox": [x, y, x + w, y + h]
            })

    return cropped_images

def extract_images_from_pdf(filepath: str) -> tuple[list[dict], list[dict]]:
    """
    Render PDF pages and extract visual regions.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    pages = convert_from_path(filepath, dpi=200)
    cropped_images, full_renders = [], []

    for i, page_img in enumerate(pages):
        page_num = i + 1
        full_renders.append({"page": page_num, "image": page_img})
        cropped_images.extend(process_page_images(page_img, page_num))

    return cropped_images, full_renders
