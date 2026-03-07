import os
import json
from fastapi import APIRouter
from fastapi.responses import FileResponse
from typing import Dict, Any

from cam_generator.cam_pdf_builder import build_cam_pdf

router = APIRouter()
REPORTS_DIR = "generated_cams"
os.makedirs(REPORTS_DIR, exist_ok=True)

def safe_val(val):
    if val is None or val == "":
        return "Not provided"
    return val

@router.post("/generate-cam/")
async def generate_cam(payload: Dict[str, Any]):
    """
    Generates LLM summaries via Five Cs prompt, renders PDF via ReportLab, and returns file download link.
    """
    features = payload.get("features", {})
    ml_output = payload.get("ml_output", {})
    gst_reconciliation = payload.get("gst_reconciliation", {})
    qualitative_adjuster = payload.get("qualitative_adjuster", {})
    loan_pricing_engine = payload.get("loan_pricing_engine", {})
    regulatory_intelligence = payload.get("regulatory_intelligence", {})
    smart_parser = payload.get("smart_parser", {})
    
    # Core mappings safely extracted for prompt
    company_name = safe_val(payload.get("companyName"))
    
    # Flat states passed from the pipeline
    base_score = payload.get("baseScore", 76)
    adjusted_score = payload.get("adjustedScore", 46)
    qualitative_delta = payload.get("qualitativeDelta", -30)
    gst_flags = payload.get("gstFlags", [])
    reconciliation_score = payload.get("reconciliationScore", 58)
    regulatory_score = payload.get("regulatoryScore", 85)
    final_risk_score = payload.get("finalScore", 46)
    
    # Optional nested variables (if tracking ML payload features)
    features = payload.get("features", {})
    ml_output = payload.get("ml_output", {})
    gst_reconciliation = payload.get("gst_reconciliation", {})
    loan_pricing_engine = payload.get("loan_pricing_engine", {})
    regulatory_intelligence = payload.get("regulatory_intelligence", {})
    smart_parser = payload.get("smart_parser", {})
    
    promoter_news_summary = safe_val(payload.get("promoter_news_summary"))
    regulatory_flags = payload.get("regulatoryFlags", [])
    regulatory_sources = payload.get("regulatorySources", [])
    
    analyst_inputs = payload.get("analystInputs", {})
    management_quality_assessment = safe_val(analyst_inputs.get("management_quality"))
    capacity_utilization = safe_val(analyst_inputs.get("capacity_utilization"))
    industry_outlook = safe_val(analyst_inputs.get("industry_outlook"))
    
    years_in_business = safe_val(features.get("years_in_business"))
    revenue = safe_val(features.get("revenue"))
    ebitda = safe_val(features.get("ebitda"))
    existing_debt = safe_val(features.get("existing_debt"))

    # Calculate DSCR inline
    dscr = "Not provided"
    ext_debt_num = features.get("existing_debt", 0)
    eb_num = features.get("ebitda", 0)
    if isinstance(ext_debt_num, (int, float)) and isinstance(eb_num, (int, float)):
        if ext_debt_num > 0:
            calc_dscr = eb_num / (ext_debt_num * 0.15)
            dscr = f"{calc_dscr:.2f}x"

    qualitative_notes = safe_val(payload.get("qualitative_adjuster", {}).get("summary_paragraph"))
    net_worth = safe_val(features.get("net_worth"))
    debt_equity_ratio = safe_val(features.get("debt_equity_ratio"))
    current_ratio = safe_val(features.get("current_ratio"))
    
    # Map gst flat score directly
    gst_reconciliation_score = safe_val(reconciliation_score)
    three_year_financials = safe_val(smart_parser.get("merged_financials"))
    collateral_value = safe_val(features.get("collateral_value"))
    collateral_type = safe_val(features.get("collateral_type"))

    # Limits and security
    loan_limit = safe_val(loan_pricing_engine.get("recommended_limit_cr", features.get("requested_limit")))
    
    security_coverage_ratio = "Not provided"
    colval_num = features.get("collateral_value", 0)
    limit_num = loan_pricing_engine.get("recommended_limit_cr", features.get("requested_limit", 0))
    if isinstance(colval_num, (int, float)) and isinstance(limit_num, (int, float)):
        if limit_num > 0:
            calc_scr = colval_num / limit_num
            security_coverage_ratio = f"{calc_scr:.2f}x"
            
    industry_outlook = safe_val(qualitative_adjuster.get("industry_outlook"))
    sector_news_summary = safe_val(payload.get("sector_news_summary"))
    rbi_regulatory_context = "All sources clean, no adverse findings" if not regulatory_flags and regulatory_score >= 80 else str(regulatory_flags)
    company_location = safe_val(payload.get("company_location"))
    
    # Use final score flat mapping for decision thresholds
    if isinstance(final_risk_score, (int, float)):
        if final_risk_score >= 70:
            decision = "APPROVE"
        elif final_risk_score >= 50:
            decision = "WATCHLIST"
        else:
            decision = "REJECT"
    else:
        decision = safe_val(ml_output.get("decision", "WATCHLIST"))
        
    shap_top_factors = safe_val(payload.get("shapValues", ml_output.get("top_features")))
    
    loan_limit_cr = safe_val(loan_pricing_engine.get("recommended_limit_cr"))
    interest_rate = safe_val(loan_pricing_engine.get("recommended_rate_pct"))
    risk_premium = safe_val(loan_pricing_engine.get("risk_premium"))
    tenure = safe_val(loan_pricing_engine.get("tenure_months"))

    prompt = f"""
    You are a senior credit analyst writing a Credit Appraisal Memo (CAM).
    Using the structured Five Cs framework, write 7 detailed sections based on this data:
    
    Data:
    Company: {company_name}
    Promoter News: {promoter_news_summary}
    Regulatory Flags: {regulatory_flags}
    Management Quality: {management_quality_assessment}
    Years in Business: {years_in_business}
    Revenue: {revenue}
    EBITDA: {ebitda}
    Existing Debt: {existing_debt}
    DSCR: {dscr}
    Capacity Utilization: {capacity_utilization}
    Qualitative Notes: {qualitative_notes}
    Net Worth: {net_worth}
    Debt/Equity Ratio: {debt_equity_ratio}
    Current Ratio: {current_ratio}
    GST Recon Score: {gst_reconciliation_score}
    GST Flags: {gst_flags}
    3-Year Financials: {three_year_financials}
    Collateral Value: {collateral_value}
    Collateral Type: {collateral_type}
    Loan Limit: {loan_limit}
    Security Coverage: {security_coverage_ratio}
    Industry Outlook: {industry_outlook}
    Sector News: {sector_news_summary}
    RBI/Reg Context: {rbi_regulatory_context}
    Location: {company_location}
    Final Risk Score: {final_risk_score}
    Decision: {decision}
    SHAP Top Factors: {shap_top_factors}
    Loan Limit (Cr): {loan_limit_cr}
    Interest Rate: {interest_rate}
    Risk Premium: {risk_premium}
    Tenure: {tenure}
    
    CRITICAL INSTRUCTION FOR EXECUTIVE SUMMARY:
    Generate the recommendation section citing these specific findings as reasons:
    1. GST: Identify the worst gap flags triggered from {gst_flags}.
    2. Qualitative: Point out analyst capacity/litigation negative marks that caused a {qualitative_delta} penalty.
    3. Regulatory: Detail the sources checked ({regulatory_sources}) outputting score {regulatory_score}.
    4. Verdict: Final score {final_risk_score}/100 is below approval threshold of 70 (or above!).  Recommendation must include:
    - Clear {decision} verdict
    - Specific conditions if WATCHLIST
    - Exact figures from the evidence above
    - What borrower must do to improve score (cite counterfactuals: reduce ITC gap, resolve litigation, improve capacity to >80%)
    
    Return ONLY a highly structured JSON object with EXACTLY these 7 keys:
    "Executive Summary", "Character (Management & Promoters)", "Capacity (Financial Repayment)", 
    "Capital (Net Worth & Leverage)", "Collateral (Security Coverage)", "Conditions (Macro & Industry)", 
    "AI Risk Insights & SHAP"
    Make the values fluent, professional paragraphs summarizing the risk factors in that domain.
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    sections = {}
    
    if api_key and api_key != "your_openai_api_key":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            res_txt = response.choices[0].message.content.strip()
            if res_txt.startswith("```json"):
                res_txt = res_txt[7:-3]
            sections = json.loads(res_txt)
        except Exception as e:
            print(f"LLM API failed: {e}")
            
    # Fallback populator
    if not sections:
        sections = {
            "Executive Summary": f"Based on a risk score of {final_risk_score}, we recommend a verdict of {decision} for a limit of {loan_limit_cr}Cr at {interest_rate}%. GST evidence uncovered multiple flags dictating severe risk. Qualitative adjustments resulted in {qualitative_delta} penalty (e.g., Capacity Utilization={capacity_utilization}%). Regulatory checks spanning {regulatory_sources} surfaced a score of {regulatory_score}. Borrower must improve working capital and resolve existing litigation to approach the passing threshold of 70.",
            "Character (Management & Promoters)": f"Management is noted as {management_quality_assessment}. Regulatory checks indicated: {rbi_regulatory_context}",
            "Capacity (Financial Repayment)": f"With revenue of {revenue} and EBITDA of {ebitda}, the DSCR is {dscr}. GST Score is {gst_reconciliation_score}.",
            "Capital (Net Worth & Leverage)": f"Net worth is {net_worth} making Debt/Equity {debt_equity_ratio}.",
            "Collateral (Security Coverage)": f"Security coverage is {security_coverage_ratio} against collateral value {collateral_value}.",
            "Conditions (Macro & Industry)": f"Industry outlook is {industry_outlook}. Sector news: {sector_news_summary}",
            "AI Risk Insights & SHAP": f"Top drivers: {shap_top_factors}"
        }

    company_safe_name = str(company_name).replace(" ", "_").replace("/", "")
    output_filename = f"CAM_{company_safe_name}.pdf"
    output_path = os.path.join(REPORTS_DIR, output_filename)
    
    build_cam_pdf(
        output_path=output_path,
        company_name=str(company_name),
        cin=safe_val(payload.get("cin")),
        date_str=payload.get("date", "Today"),
        analyst_name=payload.get("user_id", "System AI"),
        risk_score=final_risk_score if isinstance(final_risk_score, int) else 75,
        decision=str(decision),
        sections=sections,
        financials=payload.get("smart_parser", {}).get("merged_financials", {}),
        shap_chart_path=payload.get("shap_chart_path"),
        gst_data=payload.get("extractedFinancials", {}).get("gst_reconciliation", {}),
        gst_flags=gst_flags,
        regulatory_flags=regulatory_flags,
        loan_limit_cr=loan_limit_cr if isinstance(loan_limit_cr, (int, float)) else 0,
        interest_rate=interest_rate if isinstance(interest_rate, (int, float)) else 0,
        tenure_months=tenure if isinstance(tenure, int) else 12,
        conditions=loan_pricing_engine.get("sanction_terms", {}).get("conditions_precedent", ["Standard terms apply."]),
        score_waterfall={
            "baseScore": base_score,
            "reconciliationScore": reconciliation_score,
            "qualitativeDelta": qualitative_delta,
            "regulatoryScore": regulatory_score,
            "finalScore": final_risk_score
        }
    )
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            from supabase import create_client, Client
            supabase: Client = create_client(supabase_url, supabase_key)
            score_val = str(final_risk_score)
            if not score_val.replace('.', '', 1).isdigit(): score_val = "0"
            
            supabase.table("cam_reports").insert({
                "company_name": company_name,
                "credit_score": float(score_val),
                "disposition": decision,
                "pdf_path": output_path,
                "analyst_notes": "Generated by Five C's NLP Engine.",
                "user_id": payload.get("user_id")
            }).execute()
    except Exception as e:
        print(f"Failed to log CAM to History Table: {e}")
        
    return FileResponse(path=output_path, filename=output_filename, media_type='application/pdf')

@router.get("/history/")
async def fetch_cam_history(user_id: str = None):
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase import create_client, Client
            supabase: Client = create_client(supabase_url, supabase_key)
            query = supabase.table("cam_reports").select("*")
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.order("generated_at", desc=True).limit(10).execute()
            return result.data
        except Exception as e:
            pass
    return []
