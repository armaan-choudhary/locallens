import os
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path

def extract_images_from_pdf(filepath: str) -> tuple[list[dict], list[dict]]:
    """
    Renders each PDF page as a 200 DPI image using pdf2image.
    Uses cv2 to detect and crop embedded figures or diagrams using a contour-area heuristic.
    
    Returns a tuple of two lists:
    1. Cropped images: [{"page": int, "image": PIL.Image, "bbox": [x1, y1, x2, y2]}, ...]
    2. Full page renders: [{"page": int, "image": PIL.Image}]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    print(f"Rendering PDF to images at 200 DPI: {filepath}")
    pages = convert_from_path(filepath, dpi=200)

    cropped_images = []
    full_renders = []

    for page_index, page_img in enumerate(pages):
        page_num = page_index + 1
        
        # Save full page render
        full_renders.append({
            "page": page_num,
            "image": page_img
        })

        # Convert PIL Image to cv2 format (BGR)
        cv_img = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Use Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Heuristic: Region must be larger than 100x100 pixels
            if w > 100 and h > 100:
                # Optionally filter out the entire page boundary
                # if w > page_img.width * 0.9 and h > page_img.height * 0.9: continue

                # Allow slightly enlarged bounding box if needed, or exact crop
                crop_img = page_img.crop((x, y, x + w, y + h))

                cropped_images.append({
                    "page": page_num,
                    "image": crop_img,
                    "bbox": [x, y, x + w, y + h]
                })

    return cropped_images, full_renders
