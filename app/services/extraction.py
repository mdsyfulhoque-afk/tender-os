import fitz
import pytesseract
import os
from pathlib import Path
from app.config import OCR_CHAR_THRESHOLD, DATA_DIR, atomic_write_json

# Point to your Tesseract installation (adjust path if you installed it elsewhere)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_pdf(pdf_path: str, tender_id: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages_output = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Digital stream check
        if len(text.strip()) >= OCR_CHAR_THRESHOLD:
            pages_output.append({
                "page": page_num + 1,
                "method": "digital_pymupdf",
                "text": text
            })
        else:
            # Scanned stream fallback using Tesseract (Bengali + English)
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")
            
            # Run OCR with Bengali and English languages
            ocr_text = pytesseract.image_to_string(img_data, lang='ben+eng')
            
            pages_output.append({
                "page": page_num + 1,
                "method": "local_ocr_tesseract_bn_en",
                "text": ocr_text.strip()
            })
            
    out_path = DATA_DIR / tender_id / "raw_extracted_text.json"
    atomic_write_json(out_path, pages_output)
    return pages_output