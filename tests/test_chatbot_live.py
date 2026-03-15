"""
Task 3 — Live test of the Credit Chatbot chain with 4 questions.
Makes live PageIndex + OpenAI API calls.
"""
import sys, os
sys.path.insert(0, '.')

from chatbot.credit_chatbot import answer_credit_question

CREDIT_CONTEXT = {
    "company_name": "Sharma Textile Mills Pvt. Ltd.",
    "final_score": 72,
    "decision": "APPROVE",
    "loan_limit": 7.65,
    "gst_bank_match_score": 0.58,
    "gst_flags": ["CIRCULAR_TRADING_RISK", "REVENUE_MISMATCH", "SUSPICIOUS_TRANSACTIONS"],
    "debt_equity_ratio": 0.586,
    "working_capital": 58000000,
    "auditor_qualification": "unqualified",
    "revenue_trend": "FY2023: 35.0Cr, FY2024: 38.0Cr, FY2025: 42.5Cr",
    "sector_name": "Textiles"
}

DOC_ID = "pi-cmmjo68xg04il9rqnht74lnr1"

QUESTIONS = [
    {
        "label": "Q1",
        "question": "Why was the GST score only 0.58?",
        "expected_source": "GST Analysis",
        "checks": ["CIRCULAR_TRADING_RISK", "ITC", "0.58", "mismatch", "gap"]
    },
    {
        "label": "Q2",
        "question": "What is the revenue trend for this company?",
        "expected_source": "Annual Report",
        "checks": ["FY2023", "FY2025", "35", "42.5"]
    },
    {
        "label": "Q3",
        "question": "What did the auditor say about the financial statements?",
        "expected_source": "Annual Report",
        "checks": ["unqualified", "auditor", "opinion"]
    },
    {
        "label": "Q4",
        "question": "What would improve the credit score the most?",
        "expected_source": "Credit Score Data",
        "checks": ["debt", "GST", "0.58", "ratio", "improve"]
    }
]

def count_words(text):
    return len(text.split())

def run():
    print("=" * 70)
    print("CHATBOT LIVE TEST — Chunk 2.1")
    print("=" * 70)

    all_pass = True

    for q_obj in QUESTIONS:
        label = q_obj["label"]
        question = q_obj["question"]
        print(f"\n{'─'*70}")
        print(f"{label}: {question}")
        print(f"{'─'*70}")

        result = answer_credit_question(question, DOC_ID, CREDIT_CONTEXT)

        answer = result.get("answer", "")
        source = result.get("source", "")
        confidence = result.get("confidence", "")
        word_count = count_words(answer)

        print(f"ANSWER : {answer}")
        print(f"SOURCE : {source}")
        print(f"CONFIDENCE: {confidence}")
        print(f"WORD COUNT: {word_count}")

        # Verification
        checks_passed = any(kw.lower() in answer.lower() for kw in q_obj["checks"])
        len_ok = word_count <= 150
        confidence_present = confidence in ("HIGH", "MEDIUM", "LOW")

        status = "✅ PASS" if (checks_passed and len_ok and confidence_present) else "❌ FAIL"
        if not (checks_passed and len_ok and confidence_present):
            all_pass = False
            if not checks_passed:
                print(f"  ⚠ Check failed — expected one of: {q_obj['checks']}")
            if not len_ok:
                print(f"  ⚠ Answer too long: {word_count} words (max 150)")

        print(f"STATUS : {status}")

    print(f"\n{'='*70}")
    if all_pass:
        print("✅ ALL 4 QUESTIONS PASS — Chunk 2.1 complete.")
    else:
        print("❌ SOME QUESTIONS FAILED — review answers above.")
    print("=" * 70)

if __name__ == "__main__":
    run()
