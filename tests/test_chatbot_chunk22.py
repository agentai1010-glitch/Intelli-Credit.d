"""
Task 2 — Index generated CAM PDF in PageIndex and save doc ID to fixture file.
Then runs Task 3 — all 6 questions with enriched context + dual document sources.
"""
import sys, os, time
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

from chatbot.credit_chatbot import answer_credit_question
from chatbot.context_builder import build_credit_context

# ── Build enriched context ───────────────────────────────────────────────────
SESSION_DATA = {
    "company_name": "Sharma Textile Mills Pvt. Ltd.",
    "sector_name": "Textile Manufacturing",
    "baseScore": 91,
    "qualitativeDelta": -19,
    "regulatoryScore": 85,
    "reconciliationScore": 58,
    "finalScore": 72,
    "decision": "APPROVE",
    "loanLimit": "Rs.7.65Cr",
    "features": {
        "revenue": 425000000.0,
        "ebitda": 61000000.0,
        "net_worth": 140000000.0,
        "existing_debt": 82000000.0,
        "working_capital": 58000000.0,
        "debt_equity_ratio": 0.5857142857142857,
        "revenue_expense_ratio": 0.14352941176470588,
        "gst_bank_match_score": 0.58,
        "legal_flag_count": 0,
        "sector_risk_flag": 0,
        "auditor_qualification": "unqualified",
        "revenue_trend": "FY2023: Rs.35.0Cr -> FY2024: Rs.38.0Cr -> FY2025: Rs.42.5Cr (21.4% growth over 2 years)",
        "sector_name": "Textile Manufacturing"
    },
    "gstFlags": [
        {"flag": "CIRCULAR_TRADING_RISK", "severity": "HIGH", "penalty_pts": -20,
         "detail": "ITC claimed Rs.58L vs available Rs.42L — 38.1% gap exceeds 20% threshold"},
        {"flag": "REVENUE_MISMATCH", "severity": "MEDIUM", "penalty_pts": -7,
         "detail": "GST turnover Rs.3.85Cr vs bank credits Rs.3.55Cr — 8.45% gap"},
        {"flag": "SUSPICIOUS_TRANSACTIONS", "severity": "HIGH", "penalty_pts": -15,
         "detail": "3x round Rs.50L transactions on Jun-12, Jul-11, Sep-04"}
    ],
    "analystInputs": {
        "management_quality": "AVERAGE",
        "industry_outlook": "FAVORABLE",
        "pending_litigation": True,
        "capacity_utilization": 55
    },
    "improvement_paths": [
        {"action": "Resolve pending litigation", "score_gain": "+18 pts",
         "detail": "Litigation flag carries -18pt qualitative penalty"},
        {"action": "Improve GST compliance score from 0.58 to 0.75+", "score_gain": "+7 to +9 pts",
         "detail": "ITC gap reduction from 38.1% to below 20% threshold required"},
        {"action": "Reduce debt-equity ratio from 0.586x to below 0.470x", "score_gain": "+5.8 pts",
         "detail": "Achieved by retiring ~Rs.1.5Cr in short-term borrowings"}
    ],
    "loan_pricing_engine": {
        "recommended_limit_cr": 7.65,
        "recommended_rate_pct": 10.0,
        "tenure_months": 12
    }
}

CREDIT_CONTEXT = build_credit_context(SESSION_DATA)

ANNUAL_REPORT_DOC_ID = "pi-cmmjo68xg04il9rqnht74lnr1"
FIXTURE_PATH = "tests/fixtures/pageindex_cam_doc_id.txt"
CAM_PDF_PATH = "generated_cams/CAM_Sharma_Textile_Mills_Pvt._Ltd.pdf"

# ── Task 2: Index CAM PDF in PageIndex ───────────────────────────────────────
def index_cam_pdf() -> str:
    """Upload the CAM PDF to PageIndex using submit_document() and return the new doc_id."""
    pageindex_api_key = os.getenv("PAGEINDEX_API_KEY")
    if not os.path.exists(CAM_PDF_PATH):
        print(f"[TASK2] CAM PDF not found at {CAM_PDF_PATH}")
        return None

    try:
        from pageindex import PageIndexClient
        client = PageIndexClient(api_key=pageindex_api_key)
        abs_path = os.path.abspath(CAM_PDF_PATH)
        print(f"[TASK2] Uploading CAM PDF ({os.path.getsize(abs_path)//1024}KB) via submit_document()...")

        res = client.submit_document(file_path=abs_path)
        cam_doc_id = res.get("id") or res.get("doc_id") or res.get("document_id")
        if not cam_doc_id:
            print(f"[TASK2] Upload response (no id found): {res}")
            return None

        print(f"[TASK2] CAM PDF uploaded. doc_id = {cam_doc_id}")
        print("[TASK2] Waiting 15s for PageIndex to index the PDF...")
        time.sleep(15)

        os.makedirs("tests/fixtures", exist_ok=True)
        with open(FIXTURE_PATH, "w") as fh:
            fh.write(cam_doc_id)
        print(f"[TASK2] Saved CAM doc ID to {FIXTURE_PATH}")
        return cam_doc_id

    except Exception as e:
        print(f"[TASK2] PageIndex upload failed: {e}")
        return None

# ── Task 3: Run all 6 questions ──────────────────────────────────────────────
QUESTIONS = [
    {
        "label": "Q1",
        "question": "Why was the GST score only 0.58?",
        "checks": ["-20", "38.1", "58L", "CIRCULAR", "ITC", "gap"]
    },
    {
        "label": "Q2",
        "question": "What is the revenue trend for this company?",
        "checks": ["FY2023", "FY2025", "35", "42.5", "21.4"]
    },
    {
        "label": "Q3",
        "question": "What did the auditor say about the financial statements?",
        "checks": ["unqualified", "Unqualified", "auditor", "opinion"]
    },
    {
        "label": "Q4",
        "question": "What would improve the credit score the most?",
        "checks": ["+18", "+7", "+5.8", "litigation", "GST", "debt"]
    },
    {
        "label": "Q5",
        "question": "What is the complete score journey from ML base to final score?",
        "checks": ["91", "72", "penalty", "qualitative", "GST"]
    },
    {
        "label": "Q6",
        "question": "What are the three biggest improvements the company can make?",
        "checks": ["+18", "+7", "+5.8", "litigation", "GST", "debt"]
    }
]

def count_words(text):
    return len(text.split())

def run():
    print("=" * 70)
    print("CHATBOT LIVE TEST — Chunk 2.2 (Enriched Context + Dual Documents)")
    print("=" * 70)

    # Task 2: Index CAM PDF
    cam_doc_id = None
    if os.path.exists(FIXTURE_PATH):
        with open(FIXTURE_PATH) as f:
            cam_doc_id = f.read().strip()
        print(f"[TASK2] Reusing existing CAM doc ID: {cam_doc_id}")
    else:
        cam_doc_id = index_cam_pdf()

    if not cam_doc_id:
        print("[TASK2] ⚠ CAM PDF indexing failed — proceeding with annual report only.")

    print(f"\nContext: {CREDIT_CONTEXT['company_name']} | Final Score: {CREDIT_CONTEXT['final_score']} | Decision: {CREDIT_CONTEXT['decision']}")
    print(f"Annual Report doc_id: {ANNUAL_REPORT_DOC_ID}")
    print(f"CAM PDF doc_id: {cam_doc_id or 'NOT INDEXED'}\n")

    # Task 3: Run all 6 questions
    all_pass = True
    for q_obj in QUESTIONS:
        label = q_obj["label"]
        question = q_obj["question"]
        print(f"\n{'─'*70}")
        print(f"{label}: {question}")
        print(f"{'─'*70}")

        result = answer_credit_question(
            question=question,
            doc_id=ANNUAL_REPORT_DOC_ID,
            credit_context=CREDIT_CONTEXT,
            cam_doc_id=cam_doc_id
        )

        answer = result.get("answer", "")
        source = result.get("source", "")
        confidence = result.get("confidence", "")
        wc = count_words(answer)

        print(f"ANSWER     : {answer}")
        print(f"SOURCE     : {source}")
        print(f"CONFIDENCE : {confidence}")
        print(f"WORD COUNT : {wc}")

        checks_passed = any(kw.lower() in answer.lower() for kw in q_obj["checks"])
        len_ok = wc <= 150
        conf_ok = confidence in ("HIGH", "MEDIUM", "LOW")

        status = "✅ PASS" if (checks_passed and len_ok and conf_ok) else "❌ FAIL"
        if not checks_passed:
            print(f"  ⚠ Expected one of: {q_obj['checks']}")
            all_pass = False
        if not len_ok:
            print(f"  ⚠ Too long: {wc} words (max 150)")
            all_pass = False

        print(f"STATUS     : {status}")

    print(f"\n{'='*70}")
    print("✅ ALL 6 PASS — Chunk 2.2 complete." if all_pass else "❌ SOME FAILED — see above.")
    print("=" * 70)

if __name__ == "__main__":
    run()
