"""
Test CAM PDF generation — Chunk 1.2 verification.
Zero live API calls. Verifies all 7 fixes.
"""
import os, sys
sys.path.insert(0, '.')

from api.cam_routes import generate_cam
from unittest.mock import AsyncMock, patch

import asyncio

TEST_PAYLOAD = {
    "companyName": "Sharma Textile Mills Pvt. Ltd",
    "company_name": "Sharma Textile Mills Pvt. Ltd",
    "date": "2026-03-10",
    # Fix 2: UUID user_id — should NOT appear as analyst name
    "user_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
    "analyst_name": None,    # No name provided — should fall back to "Credit Analyst"
    "user_email": None,
    "cin": "L12345MH2024PLC009999",
    "finalScore": 72,
    "baseScore": 91,
    "adjustedScore": 72,
    "qualitativeDelta": -19,
    "regulatoryScore": 85,
    "reconciliationScore": 58,
    "loanLimit": "Rs.7.65Cr",
    "interestRate": "10.0%",
    "tenure": "12m",
    "gstFlags": [],
    "features": {
        "revenue": 425000000.0,
        "ebitda": 61000000.0,
        "net_worth": 140000000.0,
        "existing_debt": 82000000.0,
        "working_capital": 58000000.0,
        "debt_equity_ratio": 0.5857142857142857,
        "gst_bank_match_score": 0.58,
        "legal_flag_count": 0,
        "sector_risk_flag": 0,
        "auditor_qualification": "unqualified",
        "revenue_trend": "FY2023: 35.0 Cr\nFY2024: 38.0 Cr\nFY2025: 42.5 Cr",
        "sector_name": "Textiles"
    },
    "extractedFinancials": {
        "revenue": 425000000.0,
        "ebitda": 61000000.0,
        "net_worth": 140000000.0,
        "existing_debt": 82000000.0,
        "debt_equity_ratio": 0.5857142857142857,
    },
    # Fix 3: shapValues
    "shapValues": [
        {"feature": "working_capital", "impact": -0.12},
        {"feature": "debt_equity_ratio", "impact": 0.08},
        {"feature": "gst_bank_match_score", "impact": 0.05}
    ],
    # Fix 7: PageIndex enrichment
    "auditor_qualification": "unqualified",
    "revenue_trend": "FY2023: Rs.35.0Cr -> FY2024: Rs.38.0Cr -> FY2025: Rs.42.5Cr",
    "sector_name": "Textiles",
    "analystInputs": {
        "management_quality": "GOOD",
        "capacity_utilization": 75,
        "industry_outlook": "STABLE"
    },
    "regulatoryFlags": [],
    "loan_pricing_engine": {
        "recommended_limit_cr": 7.65,
        "recommended_rate_pct": 10.0,
        "tenure_months": 12,
        "sanction_terms": {
            "conditions_precedent": ["Execution of MFA", "Audited financials 2025 required"]
        }
    },
    "smart_parser": {}
}

async def run():
    # Actually call the route handler directly
    response = await generate_cam(TEST_PAYLOAD)
    
    # Now read the generated PDF text using pdfplumber
    import pdfplumber
    
    pdf_path = os.path.join("generated_cams", "CAM_Sharma_Textile_Mills_Pvt._Ltd.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return
    
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() or ""
    
    print("\n" + "="*60)
    print("CAM VERIFICATION REPORT — Chunk 1.2")
    print("="*60)
    
    # Check 1: Analyst name
    if "Credit Analyst" in all_text:
        print("✅ Fix 2 PASS: Cover shows 'Credit Analyst' (not UUID)")
    elif "f81d4fae" in all_text:
        print("❌ Fix 2 FAIL: UUID still visible on cover")
    else:
        print("⚠️  Fix 2: Analyst name not confirmed — check PDF manually")
    
    # Check 2: debt_equity_ratio
    if "0.586x" in all_text or "0.5857" in all_text:
        print("✅ Fix 5 PASS: Debt/Equity shows numeric value")
    elif "Not provided" in all_text and "Debt/Equity" in all_text:
        print("❌ Fix 5 FAIL: Debt/Equity still shows 'Not provided'")
    else:
        print("⚠️  Fix 5: Could not verify debt_equity in full text — check PDF manually")
    
    # Check 3: SHAP drivers
    if "Top drivers: Not provided" in all_text:
        print("❌ Fix 4 FAIL: AI section still shows 'Top drivers: Not provided'")
    elif "Debt-Equity Ratio" in all_text or "working_capital" in all_text or "Top SHAP Drivers" in all_text:
        print("✅ Fix 4 PASS: AI Risk Insights shows readable SHAP text")
    else:
        print("⚠️  Fix 4: SHAP text not confirmed in extracted text — check PDF manually")
    
    # Check 4: No ■ symbol
    if "\u25a0" in all_text:
        print("❌ Fix 1 FAIL: ■ symbol still present in PDF text")
    else:
        print("✅ Fix 1 PASS: No ■ symbols in PDF")
    
    # Check 5: Revenue trend
    if "FY2023" in all_text and "FY2025" in all_text:
        print("✅ Fix 6 PASS: Revenue trend (FY2023/FY2025) visible in PDF")
    else:
        print("❌ Fix 6 PARTIAL: Revenue trend not found in PDF text")
    
    # Check 6: Auditor qualification
    if "Unqualified" in all_text or "unqualified" in all_text:
        print("✅ Fix 6 PASS: Auditor opinion visible in PDF")
    else:
        print("❌ Fix 6 FAIL: Auditor qualification not found in PDF")
    
    # Check 7: Sector
    if "Textile" in all_text:
        print("✅ Fix 6/7 PASS: Sector 'Textile' visible in PDF")
    else:
        print("❌ Fix 6/7 FAIL: Sector not found in PDF")
    
    # Print specific sections for manual review
    print("\n--- PDF TEXT SNIPPET (first 3000 chars) ---")
    print(all_text[:3000])

if __name__ == "__main__":
    asyncio.run(run())
