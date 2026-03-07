"""
FastAPI routes for file ingest and processing.
"""
from fastapi import APIRouter, UploadFile, File
from typing import List
import os
import shutil

from ocr_pipeline.pdf_parser import extract_layout_text
from ocr_pipeline.table_extractor import extract_tables, export_tables_to_json
from ocr_pipeline.ocr_utils import run_ocr_with_tesseract
from ml_engine.smart_parser import classify_document_type, parse_by_type

router = APIRouter()
TEMP_DIR = "temp_uploads"

os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_documents(files: List[UploadFile] = File(...)):
    results = []
    
    for file in files:
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Run Layout parsing (PyMuPDF — safe, no external deps)
        try:
            text_blocks = extract_layout_text(file_path)
        except Exception as e:
            print(f"[upload] Layout extraction failed for {file.filename}: {e}")
            text_blocks = []

        # 2. Extract Tables via Camelot (requires Ghostscript — may fail on some systems)
        try:
            tables = extract_tables(file_path)
            tables_data = [t.to_dict(orient="records") for t in tables]
        except Exception as e:
            print(f"[upload] Table extraction failed for {file.filename} (Ghostscript may be missing): {e}")
            tables_data = []

        # 3. Fallback to Tesseract OCR if text extraction yielded nothing
        raw_text = ""
        if not text_blocks and not tables_data:
            try:
                raw_text = run_ocr_with_tesseract(file_path)
            except Exception as e:
                print(f"[upload] Tesseract OCR failed for {file.filename}: {e}")

        # Combine all extracted text for classification
        combined_text = raw_text
        if text_blocks:
            combined_text += " " + " ".join([b.get("text", "") for b in text_blocks])
        if tables_data:
            for t_dict in tables_data:
                for row in t_dict:
                    combined_text += " " + " ".join([str(v) for v in row.values()])

        # Classify Document using ML Smart Parser
        try:
            class_result = classify_document_type(combined_text, file.filename)
            parsed_data = parse_by_type(combined_text, class_result["document_type"])
        except Exception as e:
            print(f"[upload] Document classification/parsing failed for {file.filename}: {e}")
            class_result = {"document_type": "UNKNOWN", "confidence": 0.0}
            parsed_data = {"display": ["Error extracting fields"]}

        results.append({
            "filename": file.filename,
            "document_type": class_result["document_type"],
            "confidence": class_result["confidence"],
            "extracted_text_blocks": text_blocks,
            "extracted_tables": tables_data,
            "raw_ocr": raw_text,
            "extracted_fields": parsed_data
        })
        
    return {"status": "success", "processed_files": results}
