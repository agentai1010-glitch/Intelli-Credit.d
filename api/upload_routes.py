"""
FastAPI routes for file ingest and processing.
"""
from fastapi import APIRouter, UploadFile, File
from typing import List
import os
import shutil
import asyncio
import concurrent.futures

from ocr_pipeline.pdf_parser import extract_layout_text
from ocr_pipeline.table_extractor import extract_tables, export_tables_to_json
from ocr_pipeline.ocr_utils import run_ocr_with_tesseract
from ml_engine.smart_parser import classify_document_type, parse_by_type

router = APIRouter()
TEMP_DIR = "temp_uploads"

os.makedirs(TEMP_DIR, exist_ok=True)

def process_single_file(file_path: str, filename: str):
    # 1. Run Layout parsing (PyMuPDF — safe, no external deps)
    try:
        text_blocks = extract_layout_text(file_path)
    except Exception as e:
        print(f"[upload] Layout extraction failed for {filename}: {e}")
        text_blocks = []

    # 2. Extract Tables via Camelot (requires Ghostscript — may fail on some systems)
    try:
        tables = extract_tables(file_path)
        tables_data = [t.to_dict(orient="records") for t in tables]
    except Exception as e:
        print(f"[upload] Table extraction failed for {filename} (Ghostscript may be missing): {e}")
        tables_data = []

    # 3. Fallback to Tesseract OCR if text extraction yielded nothing
    raw_text = ""
    if not text_blocks and not tables_data:
        try:
            raw_text = run_ocr_with_tesseract(file_path)
        except Exception as e:
            print(f"[upload] Tesseract OCR failed for {filename}: {e}")

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
        from ocr_pipeline.ocr_utils import extract_document
        class_result = classify_document_type(combined_text, filename)
        filename_lower = filename.lower()
        if "annual_report" in filename_lower:
            class_result["document_type"] = "ANNUAL_REPORT"
        elif "gstr2a" in filename_lower or "gstr_2a" in filename_lower or "gstr-2a" in filename_lower:
            class_result["document_type"] = "GSTR2A"
        elif "gstr3b" in filename_lower or "gstr_3b" in filename_lower or "gstr-3b" in filename_lower:
            class_result["document_type"] = "GST_RETURN"
        elif "bank" in filename_lower:
            class_result["document_type"] = "BANK_STATEMENT"
        elif "sanction" in filename_lower:
            class_result["document_type"] = "SANCTION_LETTER"
            
        if class_result["document_type"] == "UNKNOWN":
            parsed_data = parse_by_type(combined_text, "UNKNOWN")
        else:
            parsed_data = extract_document(file_path, class_result["document_type"])
    except Exception as e:
        print(f"[upload] Document classification/parsing failed for {filename}: {e}")
        class_result = {"document_type": "UNKNOWN", "confidence": 0.0}
        parsed_data = {"display": ["Error extracting fields"]}

    return {
        "filename": filename,
        "document_type": class_result["document_type"],
        "confidence": class_result["confidence"],
        "extracted_text_blocks": text_blocks,
        "extracted_tables": tables_data,
        "raw_ocr": raw_text,
        "extracted_fields": parsed_data
    }

from fastapi import BackgroundTasks

# In-memory session cache for PageIndex doc IDs and status
pageindex_session_cache = {}
pageindex_status_cache = {} # session_id -> "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"

def index_annual_report_background(pdf_path: str, session_id: str):
    """Runs in background after upload returns. Does not block scoring."""
    import socket
    import time

    # DNS Warm-up: Try to force resolution of the domain if Python is being stubborn
    try:
        socket.gethostbyname("api.pageindex.ai.")
        socket.gethostbyname("api.pageindex.ai")
    except:
        pass

    for attempt in range(3):
        try:
            pageindex_status_cache[session_id] = "PROCESSING"
            print(f"[PAGEINDEX BACKGROUND] Starting indexing for session {session_id} (Attempt {attempt+1})")
            from ml_engine.pageindex_extractor import extract_with_pageindex
            # Submit to PageIndex and wait (cleanup=False so chatbot can use it)
            pageindex_data, doc_id = extract_with_pageindex("", pdf_path=pdf_path, cleanup=False)
            if doc_id:
                # Store the actual doc_id string for the chatbot
                pageindex_session_cache[session_id] = doc_id
                pageindex_status_cache[session_id] = "COMPLETED"
                print(f"[PAGEINDEX BACKGROUND] Complete. doc_id={doc_id} session={session_id}")
                return
            else:
                raise Exception("No doc_id returned")
        except Exception as e:
            print(f"[PAGEINDEX BACKGROUND] Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                pageindex_status_cache[session_id] = "FAILED"
                print(f"[PAGEINDEX BACKGROUND] All attempts failed for session {session_id}")

@router.get("/pageindex/status/{session_id}")
async def get_pageindex_status(session_id: str):
    status = pageindex_status_cache.get(session_id, "NOT_FOUND")
    doc_id = pageindex_session_cache.get(session_id)
    return {"status": status, "doc_id": doc_id}

@router.post("/upload/")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session_id: str = "default_session"
):
    # Save all files to temp dir synchronously for safety
    saved_files = []
    annual_report_path = None
    for file in files:
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append((file_path, file.filename))
        if "annual_report" in file.filename.lower():
            annual_report_path = file_path
            
    # Process files concurrently
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(saved_files) or 1, 10)) as pool:
        tasks = [loop.run_in_executor(pool, process_single_file, fp, fn) for fp, fn in saved_files]
        results = await asyncio.gather(*tasks)
    
    # Queue PageIndex if annual report found
    if annual_report_path:
        pageindex_status_cache[session_id] = "PENDING"
        background_tasks.add_task(index_annual_report_background, annual_report_path, session_id)
        print(f"[PAGEINDEX BACKGROUND] Queued for session {session_id}")
        
    return {"status": "success", "processed_files": list(results)}
