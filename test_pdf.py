import requests
import json
import fitz

url = "http://localhost:8000/api/v1/generate-cam/"
payload = {
    "companyName": "Sharma Textile Mills Pvt. Ltd.",
    "baseScore": 76,
    "adjustedScore": 46,
    "qualitativeDelta": -30,
    "reconciliationScore": 58,
    "regulatoryScore": 85,
    "finalScore": 46,
    "gstFlags": [
        {"flag": "REVENUE_MISMATCH", "severity": "MEDIUM", "score_penalty": -7},
        {"flag": "CIRCULAR_TRADING_RISK", "severity": "HIGH", "score_penalty": -20},
        {"flag": "SUSPICIOUS_TRANSACTIONS", "severity": "HIGH", "score_penalty": -15}
    ],
    "extractedFinancials": {
        "gst_reconciliation": {
            "gstr3b_turnover_cr": "3.85",
            "bank_credits_cr": "3.55",
            "revenue_gap_pct": "8.45",
            "itc_claimed_lakhs": "58",
            "itc_available_lakhs": "42",
            "itc_gap_pct": "38.1"
        }
    },
    "analystInputs": {
        "capacity_utilization": "5",
        "management_quality": "AVERAGE",
        "pending_litigation": True
    },
    "regulatorySources": ["MCA", "EPFO", "GSTIN", "High Court"],
    "loan_pricing_engine": {
        "recommended_limit_cr": 5,
        "recommended_rate_pct": 11.5,
        "tenure_months": 12
    }
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    pdf_path = "generated_cams/test_cam_sharma.pdf"
    with open(pdf_path, "wb") as f:
        f.write(response.content)
    print(f"PDF generated successfully: {pdf_path}")
    
    # Analyze the contents of the generated PDF
    try:
        doc = fitz.open(pdf_path)
        text = chr(10).join([page.get_text() for page in doc])
        with open("pdf_text_dump.txt", "w", encoding="utf-8") as dump:
            dump.write(text)
        
        print("\n--- Diagnostic Tests ---")
        if 'Score Waterfall Computation' in text:
            print('[PASS] TEST 1: Waterfall Table Found')
        else:
            print('[FAIL] TEST 1: Waterfall Table MISSING')
            
        if 'GST Declared' in text:
            print('[PASS] TEST 2A: GST Validation Summary Found')
        else:
            print('[FAIL] TEST 2A: GST Validation Summary MISSING')
            
        if 'REVENUE_MISMATCH' in text:
            print('[PASS] TEST 2B: GST Flags Found')
        else:
            print('[FAIL] TEST 2B: GST Flags MISSING')
            
        if '-30' in text:
            print('[PASS] TEST 3: Qualitative Penalty -30 appears in PDF')
        else:
            print('[FAIL] TEST 3: Qualitative Penalty MISSING')
            
        if '46 / REJECT' in text:
            print('[PASS] TEST 4: Final Score is 46 / REJECT')
        elif 'REJECT' in text and '46' in text:
            print('[PASS] TEST 4: Score 46 and REJECT both appear in PDF')
        else:
            print('[FAIL] TEST 4: Incorrect Final Score / Decision')
            
        print("\n--- Score/Decision occurrences in PDF ---")
        import re
        for m in re.finditer(r'(?:Risk Score|score|Score|Decision|REJECT|APPROVE|WATCHLIST)[^\n]{0,50}', text):
            print(' |', m.group(0).strip())
            
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        
else:
    print(f"Failed to generate PDF. Status: {response.status_code}, Body: {response.text}")
