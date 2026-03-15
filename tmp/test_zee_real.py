import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("\n" + "="*80)
print("PHASE 2 - ZEE ENTERTAINMENT - REAL WORLD PIPELINE TEST")
print("="*80 + "\n")

MOCK_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_documents", "zee")

# Define the 5 specific files
files_to_upload = [
    "mock_zee_annual_report.pdf",
    "mock_zee_bank_statement.pdf",
    "mock_zee_gstr3b.pdf",
    "mock_zee_gstr2a.pdf",
    "mock_zee_sanction_letter.pdf"
]

print("--- NODE 1: DOCUMENT EXTRACTION (UPLOAD) ---")
upload_responses = []

# Prepare files for the multipart upload
opened_files = []
try:
    files_payload = []
    for fname in files_to_upload:
        fpath = os.path.join(MOCK_DIR, fname)
        f = open(fpath, "rb")
        opened_files.append(f)
        files_payload.append(("files", (fname, f, "application/pdf")))
        
    res = client.post("/api/v1/upload/", files=files_payload)
    if res.status_code == 200:
        upload_data = res.json()
        print("Upload success.")
        # Flatten extracted data into document_data
        document_data = {}
        for p in upload_data.get("processed_files", []):
            ext = p.get("extracted_fields", {})
            # Merge extracted fields
            document_data.update(ext)
    else:
        print(f"Upload failed: {res.text}")
        sys.exit(1)
finally:
    for f in opened_files:
        f.close()

print("\n--- NODE 2: GST RECONCILIATION ---")
gst_payload = {}
opened_files = []
try:
    gstr3b_path = os.path.join(MOCK_DIR, "mock_zee_gstr3b.pdf")
    gstr2a_path = os.path.join(MOCK_DIR, "mock_zee_gstr2a.pdf")
    bank_path = os.path.join(MOCK_DIR, "mock_zee_bank_statement.pdf")
    
    f3b = open(gstr3b_path, "rb"); opened_files.append(f3b)
    f2a = open(gstr2a_path, "rb"); opened_files.append(f2a)
    fbank = open(bank_path, "rb"); opened_files.append(fbank)
    
    res = client.post("/api/v1/gst/reconcile/", 
        data={"company_name": "Zee Entertainment Enterprises Ltd."},
        files={
            "gstr3b_pdf": ("mock_zee_gstr3b.pdf", f3b, "application/pdf"),
            "gstr2a_pdf": ("mock_zee_gstr2a.pdf", f2a, "application/pdf"),
            "bank_statement_pdf": ("mock_zee_bank_statement.pdf", fbank, "application/pdf")
        }
    )
    if res.status_code == 200:
        gst_data = res.json()
        print(f"GST Reconciler Score: {gst_data.get('reconciliation_score')}")
        for flag in gst_data.get("flags", []):
            print(f"FLAG DETECTED: {flag}")
    else:
        print(f"GST Recon failed: {res.text}")
        gst_data = {}
finally:
    for f in opened_files:
        f.close()

print("\n--- NODE 3: EXTERNAL INTELLIGENCE (/regulatory/check) ---")
res = client.post("/api/v1/regulatory/check", json={"company_name": "Zee Entertainment Enterprises Ltd."})
if res.status_code == 200:
    reg_data = res.json()
    print(f"Regulatory Score: {reg_data.get('score')} | Flags: {len(reg_data.get('critical_flags', []))}")
else:
    print(f"External Intel failed: {res.text}")

print("\n--- NODE 4, 5, 6, 7: ML SCORING (NLP, Features, LightGBM, SHAP) ---")
score_payload = {
    "parsed_data": {
        "document_data": document_data,
        "gst_data": gst_data,
        "raw_text": "Extracted text combined from documents" # The frontend sends this if needed, feature engine uses extracted fields usually. 
        # Wait, the feature engine actually expects raw_text for NLP.
    }
}
# Actually the schema in score_routes receives parsed_data directly as the body:
# async def score_company(parsed_data: Dict[str, Any]):
# Let's combine the OCR texts.
raw_text_combined = ""
for pf in upload_data.get("processed_files", []):
    raw_text_combined += pf.get("raw_ocr", "") + "\n"
    
payload = {
    "document_data": document_data,
    "gst_data": gst_data,
    "raw_text": raw_text_combined
}

res = client.post("/api/v1/score/", json=payload)
if res.status_code == 200:
    score_res = res.json()
    prediction = score_res.get("score_result", {})
    explanation = score_res.get("explanation", {})
    print(f"Prediction: {prediction}")
    print(f"Top Features: {explanation.get('top_features', [])[:3]}")
else:
    print(f"Scoring failed: {res.text}")

print("\n--- LOAN PRICING ENGINE ---")
# The pricing engine is in recommendation_routes
res = client.post("/api/v1/recommendation/terms", json={
    "risk_score": int(prediction.get("predicted_score", 0)*100) if "predicted_score" in prediction else 50,
    "revenue": document_data.get("revenue", 8200),
    "debt": document_data.get("existing_debt", 2630),
    "ebitda": document_data.get("ebitda", 820),
    "collateral_value": 850.0,
    "gst_reconciliation_score": gst_data.get("reconciliation_score", 58.0),
    "qualitative_delta": {
        "pending_litigation": True,
        "management_quality": "AVERAGE",
        "industry_outlook": "STABLE",
        "collateral_quality": "STANDARD"
    }
})
if res.status_code == 200:
    pricing = res.json()
    print(f"Loan Pricing Engine output: {pricing}")
else:
    print(f"Loan pricing failed: {res.text}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")
