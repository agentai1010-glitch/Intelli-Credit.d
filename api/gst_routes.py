"""
FastAPI routes for GST Reconciliation.

# TABLE SETUP (run once in Supabase dashboard):
# CREATE TABLE gst_reports (
#   id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
#   user_id TEXT,
#   company_name TEXT NOT NULL,
#   reconciliation_score FLOAT,
#   recommendation TEXT,
#   flags_json JSONB,
#   circular_trading_json JSONB,
#   summary_paragraph TEXT,
#   created_at TIMESTAMPTZ DEFAULT NOW()
# );
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
import os
import shutil
import time

from ocr_pipeline.pdf_parser import extract_layout_text
from ocr_pipeline.ocr_utils import run_ocr_with_tesseract
from ml_engine.gst_reconciler import (
    extract_gstr3b_figures,
    extract_gstr2a_figures,
    extract_bank_credits,
    detect_circular_trading,
    reconcile
)

router = APIRouter()
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Pydantic Models for Response Validation
class FlagItem(BaseModel):
    type: str
    severity: str
    detail: str
    impact_on_score: int

class CircularTrading(BaseModel):
    circular_trading_detected: bool
    suspicious_patterns: List[str]
    confidence: float
    penalty: int

class GSTReconciliationResponse(BaseModel):
    company_name: str
    reconciliation_score: float
    revenue_gap_percent: float
    itc_gap_percent: float
    flags: List[FlagItem]
    circular_trading: CircularTrading
    recommendation: str
    summary_paragraph: str
    report_id: Optional[str]
    processing_time_seconds: float
    files_processed: List[str]

@router.post("/reconcile/", response_model=GSTReconciliationResponse)
async def reconcile_gst(
    company_name: str = Form(...),
    user_id: Optional[str] = Form(None),
    gstr3b_pdf: Optional[UploadFile] = File(None),
    gstr2a_pdf: Optional[UploadFile] = File(None),
    bank_statement_pdf: Optional[UploadFile] = File(None)
):
    start_time = time.time()
    
    uploaded_files = {
        "gstr3b": gstr3b_pdf,
        "gstr2a": gstr2a_pdf,
        "bank_stmt": bank_statement_pdf
    }
    
    valid_files = [k for k, v in uploaded_files.items() if v is not None]
    
    if len(valid_files) < 2:
        raise HTTPException(status_code=422, detail="Minimum: GSTR-3B + bank statement or GSTR-2A required")
        
    extracted_data = {}
    files_processed = []
    
    try:
        for file_key, upload_file in uploaded_files.items():
            if upload_file is None:
                continue
                
            file_path = os.path.join(TEMP_DIR, upload_file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
                
            raw_text = ""
            try:
                blocks = extract_layout_text(file_path)
                raw_text = " ".join([b.get("text", "") for b in blocks])
            except Exception as e:
                print(f"Layout extraction failed, trying OCR: {e}")
                
            if not raw_text.strip():
                raw_text = run_ocr_with_tesseract(file_path)
            
            if not raw_text or not raw_text.strip():
                raise HTTPException(status_code=400, detail=f"Could not extract text from {upload_file.filename}. Ensure PDF is not password protected.")
                
            extracted_data[file_key] = raw_text
            files_processed.append(upload_file.filename)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"File processing error: {e}")
        raise HTTPException(status_code=500, detail="Reconciliation processing failed")
        
    try:
        # Extract features using LLM since Regex is failing on real-world test cases
        from ml_engine.smart_parser import llm_extract_fields
        
        dict_3b = {}
        if "gstr3b" in extracted_data:
            dict_3b = llm_extract_fields(extracted_data["gstr3b"], "GST_RETURN") or {}
            
        dict_2a = {}
        if "gstr2a" in extracted_data:
            res_2a = llm_extract_fields(extracted_data["gstr2a"], "GSTR2A") or {}
            dict_2a = {
                "itc_available_from_suppliers": res_2a.get("itc_available", 0),
                "supplier_count": res_2a.get("supplier_count", 0)
            }
            
        dict_bank = extract_bank_credits(extracted_data.get("bank_stmt", "")) if "bank_stmt" in extracted_data else {}
        
        ct_results = {}
        if "bank_stmt" in extracted_data:
            ct_results = detect_circular_trading(extracted_data["bank_stmt"])
            
        recon_result = reconcile(dict_3b, dict_2a, dict_bank, circular_trading=ct_results)
        
    except Exception as e:
        print(f"Reconciliation error: {e}")
        raise HTTPException(status_code=500, detail="Reconciliation processing failed")
        
    report_id = None
    
    # Supabase Logging
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            from supabase import create_client, Client
            supabase: Client = create_client(supabase_url, supabase_key)
            
            db_response = supabase.table("gst_reports").insert({
                "user_id": user_id,
                "company_name": company_name,
                "reconciliation_score": recon_result["reconciliation_score"],
                "recommendation": recon_result["recommendation"],
                "flags_json": recon_result["flags"],
                "circular_trading_json": recon_result.get("circular_trading", {}),
                "summary_paragraph": recon_result.get("summary_paragraph", "")
            }).execute()
            
            if db_response.data and len(db_response.data) > 0:
                report_id = db_response.data[0].get("id")
    except Exception as e:
        print(f"Supabase logging failed (silently recovering): {e}")
        # Intentionally passing over the exception as requested
        
    end_time = time.time()
    
    return GSTReconciliationResponse(
        company_name=company_name,
        report_id=report_id,
        processing_time_seconds=round(end_time - start_time, 2),
        files_processed=files_processed,
        reconciliation_score=recon_result["reconciliation_score"],
        revenue_gap_percent=recon_result["revenue_gap_percent"],
        itc_gap_percent=recon_result["itc_gap_percent"],
        flags=recon_result["flags"],
        circular_trading=recon_result.get("circular_trading", {}),
        recommendation=recon_result["recommendation"],
        summary_paragraph=recon_result.get("summary_paragraph", "")
    )
    
@router.get("/history/")
async def get_gst_history(user_id: Optional[str] = None):
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supersonic_url := supabase_url:
            from supabase import create_client, Client
            supabase: Client = create_client(supersonic_url, supabase_key)
            
            query = supabase.table("gst_reports").select("id, company_name, reconciliation_score, recommendation, created_at")
            if user_id:
                query = query.eq("user_id", user_id)
                
            response = query.order("created_at", desc=True).limit(10).execute()
            
            # Map 'id' to 'report_id' for frontend consistency
            results = []
            for item in response.data:
                item["report_id"] = item.pop("id", None)
                results.append(item)
                
            return results
    except Exception as e:
        print(f"Failed to fetch GST history: {e}")
        return []
        
    return []
