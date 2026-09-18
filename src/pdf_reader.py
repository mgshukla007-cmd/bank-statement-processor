import pdfplumber

def detect_pdf_type(pdf_path):
    """
    Detects if the PDF is text-based or image-based.
    Returns 'text' or 'image'.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # If we extract more than 50 characters, consider it a text PDF
            if text and len(text.strip()) > 50:
                return "text"
    return "image"

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a text-based PDF.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text