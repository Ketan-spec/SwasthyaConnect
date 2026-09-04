"""
SwasthyaConnect — Robust Medical Document OCR & Text Extraction Engine
=======================================================================
Supports PDF documents and Image files (PNG, JPG, JPEG, BMP, TIFF).

OCR Engine Hierarchy:
1. PyMuPDF (fitz) — High speed digital PDF text extraction.
2. System Tesseract — Used if tesseract binary is present on OS.
3. EasyOCR (PyTorch) — Pure Python OCR fallback for images/scans if tesseract binary is absent.
"""

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os
import shutil

# Locate tesseract binary dynamically on Mac/Linux/Windows
TESSERACT_POSSIBLE_PATHS = [
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
    shutil.which("tesseract")
]

for tpath in TESSERACT_POSSIBLE_PATHS:
    if tpath and os.path.exists(tpath):
        pytesseract.pytesseract.tesseract_cmd = tpath
        break

_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"[OCR] EasyOCR init error: {e}")
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None

def is_tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
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

def ocr_image_with_easyocr(image_path_or_bytes) -> str:
    reader = get_easyocr_reader()
    if not reader:
        return ""
    try:
        results = reader.readtext(image_path_or_bytes, detail=0)
        return "\n".join(results).strip()
    except Exception as e:
        print(f"[OCR] EasyOCR error: {e}")
        return ""

def ocr_pdf_pages(pdf_path_or_bytes, max_pages: int = 5) -> str:
    if is_tesseract_available():
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
    else:
        # Fallback to EasyOCR for scanned PDF pages
        reader = get_easyocr_reader()
        if not reader:
            return ""
        
        if isinstance(pdf_path_or_bytes, bytes):
            doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
        else:
            doc = fitz.open(pdf_path_or_bytes)
            
        out = []
        pages = min(len(doc), max_pages)
        for i in range(pages):
            pix = doc[i].get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            txt = ocr_image_with_easyocr(img_bytes)
            out.append(txt)
            
        doc.close()
        return "\n".join(out).strip()

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)

def process_pdf_for_text(file_path: str) -> tuple[str, list[str], str]:
    """
    Unified image & PDF text processor.
    Returns (extracted_text, extraction_notes, confidence_level)
    """
    extraction_notes = []
    confidence = "high"
    
    ext = file_path.lower()
    
    # ── IMAGE FILES (PNG, JPG, JPEG, BMP, TIFF) ──────────────────────────────
    if ext.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        if is_tesseract_available():
            img = Image.open(file_path)
            extracted = clean_text(pytesseract.image_to_string(img))
            extraction_notes.append("System Tesseract OCR engine used on image file.")
            confidence = "high"
            return extracted, extraction_notes, confidence
        else:
            easy_text = clean_text(ocr_image_with_easyocr(file_path))
            if easy_text:
                extraction_notes.append("EasyOCR (Python engine) successfully parsed image.")
                confidence = "high"
                return easy_text, extraction_notes, confidence
            else:
                raise Exception("Failed to extract text from image using available OCR engines.")
    
    # ── PDF FILES ────────────────────────────────────────────────────────────
    extracted = clean_text(extract_text_pymupdf(file_path))
    
    if len(extracted) >= 50:
        extraction_notes.append("High-quality digital PDF text layer extracted via PyMuPDF.")
        confidence = "high"
        return extracted, extraction_notes, confidence

    # Scanned PDF fallback
    extraction_notes.append("Digital text layer low or empty -> Attempting OCR.")
    ocr_text = clean_text(ocr_pdf_pages(file_path, max_pages=5))
    if len(ocr_text) > len(extracted):
        extracted = ocr_text
        engine_name = "Tesseract OCR" if is_tesseract_available() else "EasyOCR"
        extraction_notes.append(f"{engine_name} successfully parsed scanned pages.")
        confidence = "medium"
    else:
        confidence = "low" if not extracted else "medium"
            
    return extracted, extraction_notes, confidence
