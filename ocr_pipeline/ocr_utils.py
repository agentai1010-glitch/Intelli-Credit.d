import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import os
import fitz
import ocrmypdf

# Suppress MuPDF error noise (incorrect startxref etc)
fitz.TOOLS.mupdf_display_errors(False)

def preprocess_image(image):
    """
    Applies preprocessing (deskew, denoise) using OpenCV.
    """
    # Convert PIL Image to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Binarization (Thresholding)
    _, thresh = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Deskewing
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return deskewed

def run_ocr_with_tesseract(pdf_path: str) -> str:
    """
    Converts scanned PDF pages to images, applies preprocessing,
    and runs Tesseract OCR.
    LIMIT: processes ONLY the first 3 pages to avoid hanging on large docs.
    """
    try:
        # Limit to first 3 pages for speed
        images = convert_from_path(pdf_path, last_page=3)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return ""
        
    combined_text = ""
    for i, image in enumerate(images):
        processed_img = preprocess_image(image)
        # Run Tesseract on processed block
        text = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 3')
        combined_text += f"\n--- Page {i + 1} ---\n"
        combined_text += text
        
    return combined_text

def ocr_with_ocrmypdf(pdf_path: str, output_path: str) -> bool:
    """
    Runs ocrmypdf to deskew and embed OCR layer in-place,
    outputting a searchable PDF.
    """
    try:
        ocrmypdf.ocr(pdf_path, output_path, deskew=True, force_ocr=True)
        return True
    except Exception as e:
        print(f"OCRmyPDF failed: {e}")
        return False

def extract_document(pdf_path: str, doc_type: str) -> dict:
    """
    Primary extraction router. Attemps Sarvam API via extract_with_sarvam -> parse_with_sarvam.
    If Sarvam fails, or any critical field is None, automatically falls back to 
    pytesseract -> parse_by_type.
    """
    from ocr_pipeline.sarvam_client import extract_with_sarvam, SarvamExtractionError
    from ml_engine.smart_parser import parse_by_type, llm_extract_fields
    from dotenv import load_dotenv
    load_dotenv()
    
    if doc_type == "ANNUAL_REPORT":
        print(f"[ROUTER] ANNUAL_REPORT \u2192 Starting dual extraction path")
        sarvam_data = {}
        # Step 1: Sarvam (Best Effort)
        try:
            raw_res = extract_with_sarvam(pdf_path)
            raw_text = raw_res.get("raw_text", "")
            if isinstance(raw_text, dict): raw_text = str(raw_text)
            sarvam_data = llm_extract_fields(raw_text, doc_type)
            print(f"[ROUTER] ANNUAL_REPORT \u2192 Sarvam extraction complete")
        except Exception as e:
            print(f"[ROUTER] ANNUAL_REPORT \u2192 Sarvam failed ({e}), trying local layout fallback")
            from ocr_pipeline.pdf_parser import extract_layout_text
            try:
                blocks = extract_layout_text(pdf_path)
                fallback_text = " ".join([b.get("text", "") for b in blocks])
                sarvam_data = llm_extract_fields(fallback_text, doc_type)
                print(f"[ROUTER] ANNUAL_REPORT \u2192 Local layout fallback complete")
            except Exception as e_inner:
                print(f"[ROUTER] ANNUAL_REPORT \u2192 All pre-PageIndex paths failed: {e_inner}")

        if sarvam_data and sarvam_data.get("revenue") and sarvam_data.get("net_worth"):
            print(f"[ROUTER] ANNUAL_REPORT \u2192 Gemini extraction successful. Returning immediately.")
            return sarvam_data

        # Step 2: PageIndex (Fallback, only if Sarvam results are incomplete)
        try:
            from ml_engine.pageindex_extractor import load_doc_id_or_submit, extract_with_pageindex
            from ml_engine.features import merge_extraction_sources
            
            print(f"[ROUTER] ANNUAL_REPORT \u2192 Gemini data incomplete, falling back to PageIndex...")
            doc_id = load_doc_id_or_submit(pdf_path)
            pageindex_data, _ = extract_with_pageindex(doc_id)
            print(f"[ROUTER] ANNUAL_REPORT \u2192 PageIndex extraction complete")

            # Step 3: Merge
            merged_data = merge_extraction_sources(sarvam_data, pageindex_data)
            print(f"[ROUTER] ANNUAL_REPORT \u2192 Sarvam + PageIndex merged")
            return merged_data

        except Exception as e:
            print(f"[ROUTER] ANNUAL_REPORT \u2192 PageIndex critical error: {e}")
            return sarvam_data if sarvam_data else {}

    # All other doc types OR ANNUAL_REPORT where primary paths failed
    try:
        raw_text = ""
        if doc_type != "ANNUAL_REPORT":
            try:
                raw_res = extract_with_sarvam(pdf_path)
                raw_text = raw_res.get("raw_text", "")
                if isinstance(raw_text, dict): raw_text = str(raw_text)
            except Exception as e_sarvam:
                print(f"[ROUTER] Sarvam failed for {doc_type} ({e_sarvam}), trying fallback...")
                raw_text = ""
        
        if not raw_text or not raw_text.strip():
            # FALLBACK Logic
            from ocr_pipeline.pdf_parser import extract_layout_text
            try:
                blocks = extract_layout_text(pdf_path)
                raw_text = " ".join([b.get("text", "") for b in blocks])
            except Exception as e:
                print(f"Fallback layout extraction failed: {e}")
                raw_text = ""
                
        if not raw_text or not raw_text.strip():
            raw_text = run_ocr_with_tesseract(pdf_path)
            
        return llm_extract_fields(raw_text, doc_type)
            
    except Exception as e:
        print(f"[FALLBACK] {doc_type} Global Error: {e}")
        return {}

