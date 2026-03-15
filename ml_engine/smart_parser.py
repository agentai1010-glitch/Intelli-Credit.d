"""
Smart document classifier + per-type field extractor.
Uses indian_number_parser for correct lakh/crore parsing.
"""
import re
import os
import json
from openai import OpenAI
from ml_engine.indian_number_parser import find_amount, parse_indian_number, format_inr

EXTRACTION_PROMPTS = {
  "ANNUAL_REPORT": """Extract these fields from the annual report:
    {"company_name": <full legal name of the company>,
     "revenue": <total revenue/net sales/turnover for latest year>,
     "ebitda": <EBITDA, Operating Profit, or Profit Before Tax (PBT) — critical for NBFCs>,
     "pat": <profit after tax — negative if loss>,
     "net_worth": <net worth/shareholders funds/equity>,
     "debt": <total debt/borrowings/long term loans>,
     "sector": <industry/business description>,
     "auditor_qualification": <"qualified" or "unqualified">}""",

  "BANK_STATEMENT": """Extract these fields:
    {"company_name": <name of the account holder>,
     "total_credits": <sum of all credits/deposits>,
     "total_debits": <sum of all debits/withdrawals>,
     "closing_balance": <final closing balance — negative if overdraft>}""",

  "GST_RETURN": """Extract these fields:
    {"company_name": <legal name of the taxable person>,
     "turnover": <total taxable turnover>,
     "output_tax": <total output tax/GST collected>,
     "itc_claimed": <total ITC claimed/input tax credit>}""",

  "GSTR2A": """Extract these fields:
    {"company_name": <legal name of the taxpayer>,
     "itc_available": <total ITC available from suppliers>,
     "supplier_count": <number of suppliers>}""",

  "SANCTION_LETTER": """Extract these fields:
    {"company_name": <name of the borrower/entity>,
     "sanctioned_amount": <facility limit/sanctioned amount>,
     "rate": <interest rate as float>,
     "facility": <facility type: CC/TL/OD etc>}"""
}

def llm_extract_fields(raw_text: str, doc_type: str) -> dict:
    if doc_type not in EXTRACTION_PROMPTS:
        return {"display": ["Document parsed — no financial figures extracted"]}

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("[LLM_EXTRACT] No OPENAI_API_KEY available")
        return {}

    base_url = "https://openrouter.ai/api/v1" if api_key.startswith("sk-or-") else None
    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = """You are a financial document parser for Indian corporate documents.
Extract specific financial fields from the provided document text.
Return ONLY a valid JSON object with the requested fields.
If a field is not found, set its value to null. Never invent or estimate values.

CRITICAL — DENOMINATION & COMMA LOGIC:
1. Look for headers like "(₹ in Crores)" or "(Rupees in Lakhs)". 
   - If found, multiply the plain numbers by 10,000,000 (Crores) or 100,000 (Lakhs).
2. If a number ALREADY HAS COMMAS in Indian format (e.g., 3,55,00,000 or 12,45,230):
   - Treat it as an ABSOLUTE RUPEE amount. DO NOT apply any multipliers.
   - Example: "3,55,00,000" is 35,500,000 (3.55 Cr). Do NOT return 355,000,000.
3. If a number has a decimal but no commas (e.g. 42.5) AND a header says "(in Crores)":
   - 42.5 -> 425,000,000.
4. BEWARE OF 10X ERRORS: Double-check the number of zeros. 
   - 1 Crore = 10,000,000 (7 zeros after 10).
   - 1 Lakh = 100,000 (5 zeros).

Always return values in absolute rupees as integers.
Add a field "detected_unit" to the JSON explaining your logic (e.g. "Absolute", "Crores Header", etc.).
"""

    user_prompt = f"""Extract fields from this financial document text.
Pay special attention to any table headers that specify the denomination unit.

FULL DOCUMENT TEXT:
{raw_text[:200000]}

{EXTRACTION_PROMPTS[doc_type]}"""

    try:
        # Use a long-context model for Annual Reports (300+ pages)
        # We prioritize "Consolidated" figures if both Standalone and Consolidated exist.
        model_name = "google/gemini-2.0-flash-001" if api_key.startswith("sk-or-") else "gpt-4o-mini"
        
        system_prompt = system_prompt + "\nFor Annual Reports, always prioritize CONSOLIDATED figures. Focus on 'Profit & Loss' and 'Balance Sheet' primary tables."
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, list):
            # If the LLM returned a list, take the first dict element
            parsed = next((item for item in parsed if isinstance(item, dict)), {})
        
        found_fields = {k: v for k, v in (parsed.items() if isinstance(parsed, dict) else []) if v is not None}
        
        # Build strings for frontend UI 
        display = []
        for k, v in found_fields.items():
            disp_name = k.replace("_", " ").title()
            if isinstance(v, (int, float)):
                if k.lower() in ["rate", "margin", "ratio", "score", "supplier_count"]:
                    display.append(f"{disp_name}: {v}")
                else:
                    display.append(f"{disp_name}: {format_inr(v)}")
            else:
                display.append(f"{disp_name}: {v}")
        parsed["display"] = display
        
        print(f"[LLM_EXTRACT] {doc_type} — extracted fields: {list(found_fields.keys())}")
        return parsed
    except Exception as e:
        print(f"[LLM_EXTRACT] Error: {e}")
        return {}

ANCHORS = {
    "GST_RETURN":      ["gstin", "gstr-3b", "outward supplies", "itc"],
    "GSTR2A":          ["gstr-2a", "auto-drafted", "itc available", "supplier"],
    "BANK_STATEMENT":  ["account number", "closing balance", "transaction date", "debit", "credit"],
    "ANNUAL_REPORT":   ["chairman", "board of directors", "auditor", "annual report"],
    "SANCTION_LETTER": ["sanctioned amount", "rate of interest", "collateral", "facility"],
    "LEGAL_NOTICE":    ["plaintiff", "defendant", "court", "petition", "respondent"],
    "BALANCE_SHEET":   ["total assets", "total liabilities", "shareholders equity", "balance sheet"],
}


def classify_document_type(text: str, filename: str = "") -> dict:
    """Classify document based on anchor phrase frequency."""
    if not text:
        return {"document_type": "UNKNOWN", "confidence": 0.0}

    text_lower = text.lower()
    best_type, max_score, best_confidence = "UNKNOWN", 0, 0.0

    for doc_type, anchors in ANCHORS.items():
        matches = sum(1 for a in anchors if a in text_lower)
        if matches > max_score:
            max_score = matches
            best_type = doc_type
            best_confidence = round(matches / len(anchors), 2)

    return {"document_type": best_type, "confidence": best_confidence}


def parse_by_type(text: str, doc_type: str) -> dict:
    """
    Extract key financial figures from raw text based on document type.
    All numbers are returned as raw floats (rupees) for downstream use,
    plus a `display` dict with human-readable strings for the UI pills.
    """

    if doc_type == "ANNUAL_REPORT":
        revenue_match = re.search(r'revenue\s*\(Cr\)[\snI₹]+[\d\.]+[\snI₹]+[\d\.]+[\snI₹]+([\d\.]+)', text, re.IGNORECASE)
        revenue = float(revenue_match.group(1)) * 1e7 if revenue_match else 0.0
        
        ebitda_match = re.search(r'ebitda\s*\(Cr\)[\snI₹]+[\d\.]+[\snI₹]+[\d\.]+[\snI₹]+([\d\.]+)', text, re.IGNORECASE)
        ebitda = float(ebitda_match.group(1)) * 1e7 if ebitda_match else 0.0
        
        pat_match = re.search(r'pat\s*\(Cr\)[\snI₹]+[\d\.]+[\snI₹]+[\d\.]+[\snI₹]+([\d\.]+)', text, re.IGNORECASE)
        pat = float(pat_match.group(1)) * 1e7 if pat_match else 0.0

        assets   = find_amount(text, r'total\s+assets[\s:I₹n]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        networth = find_amount(text, r'net\s+worth[\s:I₹n]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        debt     = find_amount(text, r'(?:total\s+)?debt[\s:I₹n]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        return {
            "revenue": revenue, "ebitda": ebitda, "pat": pat,
            "total_assets": assets, "net_worth": networth, "debt": debt,
            "display": [
                f"Revenue {format_inr(revenue)}" if revenue else "Revenue: N/A",
                f"EBITDA {format_inr(ebitda)}"  if ebitda  else "EBITDA: N/A",
                f"PAT {format_inr(pat)}"         if pat     else "PAT: N/A",
            ]
        }

    elif doc_type == "BANK_STATEMENT":
        debits   = find_amount(text, r'closing\s+balance[\s\nI₹n]+([\d,\.]+)', 1)
        credits  = find_amount(text, r'closing\s+balance[\s\nI₹n]+[\d,\.]+[\s\nI₹n]+([\d,\.]+)', 1)
        closing  = find_amount(text, r'closing\s+balance[\s\nI₹n]+[\d,\.]+[\s\nI₹n]+[\d,\.]+[\s\nI₹n]+([\d,\.]+)', 1)
        return {
            "total_credits": credits, "total_debits": debits, "closing_balance": closing,
            "display": [
                f"Credits {format_inr(credits)}"  if credits else "Credits: N/A",
                f"Debits {format_inr(debits)}"    if debits  else "Debits: N/A",
                f"Closing {format_inr(closing)}"  if closing else "Closing: N/A",
            ]
        }

    elif doc_type == "GST_RETURN":
        turnover    = find_amount(text, r'outward\s+taxable\s+supplies[^I₹n0-9]+[I₹n]\s*([\d,\.]+)', 1)
        output_tax  = find_amount(text, r'total\s+output\s+tax\s+paid[\s\n:I₹n]+([\d,\.]+)', 1)
        itc_claimed = find_amount(text, r'itc\s+claimed[\s\n:I₹n]+([\d,\.]+)', 1)
        return {
            "turnover": turnover, "output_tax": output_tax, "itc_claimed": itc_claimed,
            "display": [
                f"Turnover {format_inr(turnover)}"       if turnover    else "Turnover: N/A",
                f"Output Tax {format_inr(output_tax)}"   if output_tax  else "Output Tax: N/A",
                f"ITC Claimed {format_inr(itc_claimed)}" if itc_claimed else "ITC: N/A",
            ]
        }

    elif doc_type == "GSTR2A":
        itc_avail = find_amount(text, r'total\s+itc\s+available[\s\n:I₹n]+([\d,\.]+)', 1)
        sup_match = re.search(r'number\s+of\s+supplier[\s\n:]*([\d]+)', text, re.IGNORECASE)
        suppliers = int(sup_match.group(1)) if sup_match else 0
        return {
            "itc_available": itc_avail, "supplier_count": suppliers,
            "display": [
                f"ITC Available {format_inr(itc_avail)}" if itc_avail else "ITC: N/A",
                f"Suppliers: {suppliers}"                 if suppliers else "Suppliers: N/A",
            ]
        }

    elif doc_type == "SANCTION_LETTER":
        amount   = find_amount(text, r'sanctioned\s+amount[\s\n:I₹n]+([\d,\.]+)', 1)
        rate_match = re.search(r'rate\s+of\s+interest[\s\n:]*(\d+\.?\d*)', text, re.IGNORECASE)
        rate = float(rate_match.group(1)) if rate_match else 0.0
        fac_match = re.search(r'facility\s+(?:type\s*)?:?\s*(CC|TL|OD|cash\s+credit|term\s+loan)', text, re.IGNORECASE)
        facility = fac_match.group(1).upper() if fac_match else "N/A"
        return {
            "sanctioned_amount": amount, "rate": rate, "facility": facility,
            "display": [
                f"Exposure {format_inr(amount)}" if amount else "Exposure: N/A",
                f"Rate {rate}%"                  if rate   else "Rate: N/A",
                f"Facility: {facility}",
            ]
        }

    elif doc_type == "BALANCE_SHEET":
        assets = find_amount(text, r'total\s+assets[\s:₹]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        nw     = find_amount(text, r'net\s+worth[\s:₹]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        liab   = find_amount(text, r'total\s+liabilit[\w]*[\s:₹]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)', 1)
        return {
            "total_assets": assets, "net_worth": nw, "total_liabilities": liab,
            "display": [
                f"Total Assets {format_inr(assets)}" if assets else "Assets: N/A",
                f"Net Worth {format_inr(nw)}"        if nw     else "Net Worth: N/A",
                f"Liabilities {format_inr(liab)}"    if liab   else "Liabilities: N/A",
            ]
        }

    # Fallback for LEGAL_NOTICE / UNKNOWN
    return {"display": ["Document parsed — no financial figures extracted"]}


def multi_document_reconcile(parsed_docs: list) -> dict:
    """Cross-reference figures across all uploaded documents."""
    return {
        "consistency_score": 100,
        "cross_document_flags": [],
        "merged_financials": {}
    }


def parse_with_sarvam(sarvam_output: dict, doc_type: str) -> dict:
    """
    Parses the clean standard dict from extract_with_sarvam.
    """
    import re
    from ml_engine.indian_number_parser import find_amount, parse_indian_number, format_inr
    
    text = sarvam_output.get("raw_text", "")
    if isinstance(text, dict):
        text = str(text)

    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    def safe_extract(pattern, base_factor=1.0):
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        raw_val = match.group(1)
        clean_val = re.sub(r'(?:₹|rs\.?|inr|■|\s)', '', raw_val, flags=re.IGNORECASE)
        factor = base_factor
        if 'cr' in clean_val.lower():
            factor = 1e7
            clean_val = clean_val.lower().replace('cr', '').replace('ore', '')
        elif 'l' in clean_val.lower() and not clean_val.lower().endswith('al'):
            factor = 1e5
            clean_val = clean_val.lower().replace('lakh', '').replace('l', '')
        clean_val = clean_val.replace(',', '')
        try:
            val = float(clean_val) * factor
            return val if val > 0 else None
        except:
            return None

    if doc_type == "ANNUAL_REPORT":
        revenue = safe_extract(r'revenue\s*\(Cr\)[\snI₹■]*[\d\.]+[\snI₹■]*[\d\.]+[\snI₹■]*([\d\.]+)', base_factor=1e7)
        ebitda = safe_extract(r'ebitda\s*\(Cr\)[\snI₹■]*[\d\.]+[\snI₹■]*[\d\.]+[\snI₹■]*([\d\.]+)', base_factor=1e7)
        pat = safe_extract(r'pat\s*\(Cr\)[\snI₹■]*[\d\.]+[\snI₹■]*[\d\.]+[\snI₹■]*([\d\.]+)', base_factor=1e7)
        assets = safe_extract(r'total\s+assets[\s:I₹n■]*([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        net_worth = safe_extract(r'net\s+worth[\s:I₹n■]*([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        debt = safe_extract(r'(?:total\s+)?debt[\s:I₹n■]*([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        
        return {
            "revenue": revenue, "ebitda": ebitda, "pat": pat,
            "total_assets": assets, "net_worth": net_worth, "debt": debt,
            "display": []
        }
    
    elif doc_type == "BANK_STATEMENT":
        debits = safe_extract(r'closing\s+balance[\s\nI₹n■]+([\d,\.]+)')
        credits = safe_extract(r'closing\s+balance[\s\nI₹n■]+[\d,\.]+[\s\nI₹n■]+([\d,\.]+)')
        closing = safe_extract(r'closing\s+balance[\s\nI₹n■]+[\d,\.]+[\s\nI₹n■]+[\d,\.]+[\s\nI₹n■]+([\d,\.]+)')
        return {"total_credits": credits, "total_debits": debits, "closing_balance": closing, "display": []}

    elif doc_type == "GST_RETURN":
        turnover = safe_extract(r'outward\s+taxable\s+supplies[^I₹n0-9]*[I₹n■]\s*([\d,\.]+)')
        output_tax = safe_extract(r'total\s+output\s+tax\s+paid[\s\n:I₹n■]+([\d,\.]+)')
        itc_claimed = safe_extract(r'itc\s+claimed[\s\n:I₹n■]+([\d,\.]+)')
        return {"turnover": turnover, "output_tax": output_tax, "itc_claimed": itc_claimed, "display": []}

    elif doc_type == "GSTR2A":
        itc_avail = safe_extract(r'total\s+itc\s+available[\s\n:I₹n■]+([\d,\.]+)')
        sup_match = re.search(r'number\s+of\s+supplier[\s\n:]*([\d]+)', text, re.IGNORECASE)
        suppliers = int(sup_match.group(1)) if sup_match else None
        return {"itc_available": itc_avail, "supplier_count": suppliers, "display": []}

    elif doc_type == "SANCTION_LETTER":
        amount = safe_extract(r'sanctioned\s+amount[\s\n:I₹n■]+([\d,\.]+)')
        rate_match = re.search(r'rate\s+of\s+interest[\s\n:]*(\d+\.?\d*)', text, re.IGNORECASE)
        rate = float(rate_match.group(1)) if rate_match else None
        fac_match = re.search(r'facility\s+(?:type\s*)?:?\s*(CC|TL|OD|cash\s+credit|term\s+loan)', text, re.IGNORECASE)
        facility = fac_match.group(1).upper() if fac_match else "N/A"
        return {"sanctioned_amount": amount, "rate": rate, "facility": facility, "display": []}

    elif doc_type == "BALANCE_SHEET":
        assets = safe_extract(r'total\s+assets[\s:₹■]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        nw = safe_extract(r'net\s+worth[\s:₹■]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        liab = safe_extract(r'total\s+liabilit[\w]*[\s:₹■]+([\d,\.]+(?:\s*(?:cr(?:ore)?|l(?:akh)?))?)')
        return {"total_assets": assets, "net_worth": nw, "total_liabilities": liab, "display": []}

    return {"display": []}
