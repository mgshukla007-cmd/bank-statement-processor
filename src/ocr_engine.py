import pytesseract
from pdf2image import convert_from_path

# Windows users: if Tesseract is not on PATH, uncomment and fix the path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image_pdf(pdf_path):
    """
    Converts an image-based PDF to images, then runs OCR via Tesseract.
    Returns empty string if Tesseract is not installed (graceful fallback).
    """
    try:
        images = convert_from_path(pdf_path, dpi=300)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang="eng") + "\n"
        return text
    except Exception as e:
        # Graceful degradation: OCR unavailable -> return empty text
        # The UI will show a clear message instead of crashing.
        print(f"[OCR] Tesseract not available or failed: {e}")
        return ""