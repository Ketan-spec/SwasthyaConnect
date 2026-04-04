import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os

# Tesseract setup for macOS (usually /opt/homebrew/bin/tesseract or /usr/local/bin/tesseract)
# If it's in PATH, we don't strictly need to set tesseract_cmd unless it fails.
TESS_PATH_MAC_1 = "/opt/homebrew/bin/tesseract"
TESS_PATH_MAC_2 = "/usr/local/bin/tesseract"

if os.path.exists(TESS_PATH_MAC_1):
    pytesseract.pytesseract.tesseract_cmd = TESS_PATH_MAC_1
elif os.path.exists(TESS_PATH_MAC_2):
    pytesseract.pytesseract.tesseract_cmd = TESS_PATH_MAC_2

def is_tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

def extract_text_pymupdf(pdf_path_or_bytes) -> str:
    if isinstance(pdf_path_or_bytes, bytes):
        doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(pdf_path_or_bytes)
        
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    doc.close()
    return "\n".join(pages_text).strip()

def ocr_pdf_pages(pdf_path_or_bytes, max_pages: int = 3) -> str:
    if not is_tesseract_available():
        return ""
        
    if isinstance(pdf_path_or_bytes, bytes):
        doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(pdf_path_or_bytes)
        
    out = []
    pages = min(len(doc), max_pages)

    for i in range(pages):
        pix = doc[i].get_pixmap(dpi=220)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        out.append(pytesseract.image_to_string(img))

    doc.close()
    return "\n".join(out).strip()

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)

def process_pdf_for_text(file_path: str) -> tuple[str, list[str], str]:
    """
    Returns (extracted_text, extraction_notes, confidence_level)
    """
    extraction_notes = []
    confidence = "high"
    
    ext = file_path.lower()
    
    if ext.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        if not is_tesseract_available():
            raise Exception("Tesseract OCR is not installed. Please install it on your Mac to read images.")
        img = Image.open(file_path)
        extracted = clean_text(pytesseract.image_to_string(img))
        extraction_notes.append("Native OCR used on image file.")
        confidence = "medium"
        return extracted, extraction_notes, confidence
    
    extracted = clean_text(extract_text_pymupdf(file_path))
    
    if len(extracted) < 300:
        extraction_notes.append("Selectable text was very low -> attempting OCR on first pages.")
        confidence = "medium"
        
        if not is_tesseract_available():
            extraction_notes.append("OCR not available (Tesseract not found).")
            confidence = "low"
        else:
            ocr_text = clean_text(ocr_pdf_pages(file_path, max_pages=3))
            if len(ocr_text) > len(extracted):
                extracted = ocr_text
                extraction_notes.append("OCR text used (first 3 pages).")
            else:
                extraction_notes.append("OCR output was not better than extracted text.")
                confidence = "low"
                
    return extracted, extraction_notes, confidence
