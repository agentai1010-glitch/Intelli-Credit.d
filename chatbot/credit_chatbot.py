"""
Credit Intelligence Chatbot — Node 8 in the Intelli-Credit pipeline.
Uses PageIndex (annual report + CAM PDF) for retrieval and GPT-4o Mini for synthesis.
"""
import os
import time
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ANNUAL_REPORT_DOC_ID = "pi-cmmjo68xg04il9rqnht74lnr1"


def _query_pageindex(client, doc_id: str, question: str) -> str:
    """Query a single PageIndex doc and return the text excerpt."""
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
            res = client.chat_completions(
                messages=[{
                    "role": "user",
                    "content": (
                        f"{question} "
                        "Retrieve the exact text from the document most relevant to this question. "
                        "Return the relevant passage as a direct quote."
                    )
                }],
                doc_id=doc_id,
                temperature=0.0
            )
            if isinstance(res, dict) and "choices" in res:
                content = res["choices"][0]["message"].get("content", "").strip()
                if content and content.lower() not in ("none", "not found", ""):
                    return content
                return "" # Found nothing relevant
        except Exception as e:
            print(f"[CHATBOT] PageIndex query attempt {attempt+1} failed for doc {doc_id}: {e}")
            if attempt < 2:
                time.sleep(2)
    return ""


def answer_credit_question(
    question: str,
    doc_id: str,
    credit_context: dict,
    cam_doc_id: str = None
) -> dict:
    """
    Answer an analyst's natural-language question about a credit decision.

    Parameters
    ----------
    question       : Analyst's natural-language question
    doc_id         : PageIndex document ID (indexed annual report)
    credit_context : Rich structured dict from context_builder.build_credit_context()
    cam_doc_id     : Optional PageIndex doc ID for the generated CAM PDF

    Returns
    -------
    {"answer": str, "source": str, "confidence": "HIGH"|"MEDIUM"|"LOW"}
    """
    pageindex_api_key = os.getenv("PAGEINDEX_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # ── Step 1: Query PageIndex across both documents ───────────────────────
    annual_report_excerpt = ""
    cam_excerpt = ""
    confidence = "LOW"
    source = "Credit Score Data"

    try:
        from pageindex import PageIndexClient
        pi_client = PageIndexClient(api_key=pageindex_api_key)

        annual_report_excerpt = _query_pageindex(pi_client, doc_id, question)
        if cam_doc_id:
            cam_excerpt = _query_pageindex(pi_client, cam_doc_id, question)
    except Exception as e:
        print(f"[CHATBOT] PageIndex init failed: {e}")

    # Merge both excerpts — truncate each to 600 chars to prevent prompt overflow
    MAX_EXCERPT = 600
    annual_report_excerpt = annual_report_excerpt[:MAX_EXCERPT] if annual_report_excerpt else ""
    cam_excerpt = cam_excerpt[:MAX_EXCERPT] if cam_excerpt else ""

    if annual_report_excerpt and cam_excerpt:
        merged_context = f"[Annual Report]\n{annual_report_excerpt}\n\n[CAM PDF]\n{cam_excerpt}"
        confidence = "HIGH"
        source = "Annual Report + CAM PDF"
    elif annual_report_excerpt:
        merged_context = f"[Annual Report]\n{annual_report_excerpt}"
        confidence = "HIGH"
        source = "Annual Report"
    elif cam_excerpt:
        merged_context = f"[CAM PDF]\n{cam_excerpt}"
        confidence = "HIGH"
        source = "CAM PDF"
    else:
        merged_context = "(No direct document excerpt found — answering from structured credit facts.)"
        confidence = "MEDIUM" if credit_context else "LOW"

    # ── Step 2: Determine source from question keywords ─────────────────────
    q_lower = question.lower()
    if any(kw in q_lower for kw in ("gst", "itc", "reconciliation", "tax", "turnover mismatch", "itc gap")):
        source = "GST Analysis"
    elif any(kw in q_lower for kw in ("waterfall", "journey", "score", "91", "base", "breakdown", "how did")):
        source = "CAM PDF" if cam_excerpt else "Credit Score Data"
    elif any(kw in q_lower for kw in ("improve", "increase score", "what would", "recommendation", "biggest")):
        source = "Credit Score Data"
    elif annual_report_excerpt:
        source = "Annual Report"

    if credit_context:
        confidence = max(confidence, "MEDIUM", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])

    # ── Step 3: Build enriched system prompt ────────────────────────────────
    ctx = credit_context

    # Format ML features for prompt
    ml_feat_lines = []
    for feat, detail in ctx.get("ml_features", {}).items():
        ml_feat_lines.append(
            f"  • {feat}: {detail.get('value')} [{detail.get('signal')}] — {detail.get('meaning')}"
        )
    ml_features_str = "\n".join(ml_feat_lines) or "N/A"

    # Format GST flags
    gst_flag_lines = []
    for f in ctx.get("gst_flags", []):
        gst_flag_lines.append(
            f"  • {f.get('flag')} ({f.get('severity')}, {f.get('penalty_pts')} pts): {f.get('detail', '')}"
        )
    gst_flags_str = "\n".join(gst_flag_lines) or "None"

    # Format qualitative adjustments
    qual_lines = []
    for q in ctx.get("qualitative_adjustments", []):
        impact = q.get("impact", 0)
        sign = "+" if impact > 0 else ""
        qual_lines.append(f"  • {q.get('factor')}: {q.get('rating')} → {sign}{impact} pts")
    qual_str = "\n".join(qual_lines) or "N/A"

    # Format improvement paths
    imp_lines = []
    for i, imp in enumerate(ctx.get("improvement_paths", []), 1):
        imp_lines.append(
            f"  {i}. {imp.get('action')} → {imp.get('score_gain')}: {imp.get('detail', '')}"
        )
    imp_str = "\n".join(imp_lines) or "N/A"

    system_prompt = f"""You are a credit analyst assistant helping a bank officer understand a credit decision for {ctx.get('company_name', 'the applicant')} ({ctx.get('sector', 'Unknown Sector')}).

DOCUMENT EVIDENCE (retrieved from PageIndex):
{merged_context}

SCORE WATERFALL:
  ML Base Score: {ctx.get('base_ml_score', 91)}
  GST Penalty: {ctx.get('gst_penalty', -8)} pts (GST reconciliation score = {ctx.get('gst_reconciliation_score', 58)}/100)
  Qualitative Penalty: {ctx.get('qualitative_penalty', -19)} pts
  Regulatory Impact: {ctx.get('regulatory_impact', 0)} pts
  FINAL SCORE: {ctx.get('final_score', 72)} → {ctx.get('decision', 'APPROVE')}

LOAN TERMS: Rs.{ctx.get('loan_limit_cr', 7.65)}Cr @ {ctx.get('interest_rate', 10.0)}% for {ctx.get('tenure_months', 12)} months

6 ML FEATURES:
{ml_features_str}

GST ANALYSIS:
  Reconciliation Score: {ctx.get('gst_reconciliation_score', 58)}/100
  GST Score Formula: {ctx.get('gst_formula', 'N/A')}
  Flags:
{gst_flags_str}

QUALITATIVE ADJUSTMENTS:
{qual_str}

ENRICHMENT (from Annual Report via PageIndex):
  Auditor Opinion: {ctx.get('auditor_qualification', 'Unqualified')}
  Revenue Trend: {ctx.get('revenue_trend', 'N/A')}

IMPROVEMENT PATHS TO HIGHER SCORE:
{imp_str}

RULES:
1. Answer in EXACTLY 3-5 sentences. HARD LIMIT: 120 words maximum. Stop after 120 words.
2. ALWAYS cite the specific number (e.g., "-20 pts", "38.1% ITC gap", "Rs.7.65Cr").
3. Never invent numbers — use ONLY the facts above.
4. Reference the document evidence when it is relevant.
5. For score journey questions: trace each step (base → GST penalty → qualitative → final) in one sentence each.
6. For improvement questions: list all 3 paths with their exact point gains in bullet format.
"""

    print(f"\n[CHATBOT SOURCE] Question: {question[:60]}")
    print(f"[CHATBOT SOURCE] PageIndex annual report excerpt: {bool(annual_report_excerpt)}, CAM excerpt: {bool(cam_excerpt)}")

    answer = "Unable to generate an answer at this time."

    # ── Step 4: Call GPT-4o Mini via OpenRouter or OpenAI ───────────────────
    if openai_api_key and openai_api_key not in ("your_openai_api_key", ""):
        try:
            from openai import OpenAI
            if str(openai_api_key).startswith("sk-or-"):
                oai = OpenAI(api_key=openai_api_key, base_url="https://openrouter.ai/api/v1")
            else:
                oai = OpenAI(api_key=openai_api_key)

            response = oai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.2,
                max_tokens=180
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[CHATBOT] LLM call failed: {e}")
            answer = _build_fallback_answer(question, credit_context, merged_context)
    else:
        answer = _build_fallback_answer(question, credit_context, merged_context)
        confidence = "MEDIUM"

    return {
        "answer": answer,
        "source": source,
        "confidence": confidence
    }


def _build_fallback_answer(question: str, ctx: dict, doc_excerpt: str) -> str:
    """Grounded rule-based fallback when LLM is unavailable."""
    q = question.lower()
    flags = ctx.get("gst_flags", [])
    flag_names = ", ".join(f.get("flag", "") for f in flags) or "CIRCULAR_TRADING_RISK, REVENUE_MISMATCH"
    gst_match = ctx.get("ml_features", {}).get("gst_bank_match_score", {}).get("value", "0.58")
    der = ctx.get("ml_features", {}).get("debt_equity_ratio", {}).get("value", "0.586x")
    imps = ctx.get("improvement_paths", [])

    if "gst" in q or "itc" in q or "reconciliation" in q:
        f1 = next((f for f in flags if "CIRCULAR" in f.get("flag", "")), {})
        f2 = next((f for f in flags if "REVENUE" in f.get("flag", "")), {})
        f3 = next((f for f in flags if "SUSPICIOUS" in f.get("flag", "")), {})
        return (
            f"The GST reconciliation score of {ctx.get('gst_reconciliation_score', 58)}/100 reflects three flags: "
            f"{f1.get('flag', 'CIRCULAR_TRADING_RISK')} (-20 pts): {f1.get('detail', 'ITC gap 38.1%')}; "
            f"{f2.get('flag', 'REVENUE_MISMATCH')} (-7 pts): {f2.get('detail', '8.45% turnover gap')}; "
            f"{f3.get('flag', 'SUSPICIOUS_TRANSACTIONS')} (-15 pts): {f3.get('detail', '3 round transactions')}. "
            f"Formula: {ctx.get('gst_formula', '100 - 20 - 7 - 15 = 58/100')}."
        )
    elif "revenue" in q or "trend" in q:
        return (
            f"Revenue trend: {ctx.get('revenue_trend', 'FY2023: Rs.35Cr → FY2024: Rs.38Cr → FY2025: Rs.42.5Cr')}. "
            f"Source: Annual Report (Financial Metrics Table)."
        )
    elif "auditor" in q or "audit" in q:
        return (
            f"The auditor provided an {ctx.get('auditor_qualification', 'Unqualified')} opinion on the financial statements "
            f"of {ctx.get('company_name', 'the company')}. Source: Annual Report (Auditor's Report)."
        )
    elif "waterfall" in q or "journey" in q or ("score" in q and ("91" in q or "base" in q or "how" in q)):
        return (
            f"Score journey: ML Base = {ctx.get('base_ml_score', 91)} → "
            f"GST penalty = {ctx.get('gst_penalty', -8)} pts (GST score {ctx.get('gst_reconciliation_score', 58)}/100) → "
            f"Qualitative penalty = {ctx.get('qualitative_penalty', -19)} pts → "
            f"Regulatory = {ctx.get('regulatory_impact', 0)} pts → "
            f"Final = {ctx.get('final_score', 72)} ({ctx.get('decision', 'APPROVE')})."
        )
    elif "improve" in q or "biggest" in q or "increase" in q:
        lines = [f"{i+1}. {imp.get('action')} → {imp.get('score_gain')}" for i, imp in enumerate(imps[:3])]
        return "Top 3 improvements: " + "; ".join(lines) + ". Source: Credit Score Data (SHAP + Counterfactual Analysis)."
    else:
        return (
            f"{ctx.get('company_name', 'The company')} received a score of {ctx.get('final_score')} "
            f"with decision {ctx.get('decision')} for Rs.{ctx.get('loan_limit_cr')}Cr. "
            f"{doc_excerpt[:150] if doc_excerpt else ''}"
        )
