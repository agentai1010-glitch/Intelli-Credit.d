import re
import pandas as pd
import numpy as np

def parse_indian_number(text: str) -> float:
    """
    Parses strings containing Indian number formats (e.g., '1,00,000.50') into floats.
    """
    if not text:
        return 0.0
    # Extract digits, commas, and at most one decimal point
    clean_str = re.sub(r'[^\d\.,]', '', str(text))
    if not clean_str:
        return 0.0
    # Remove commas
    clean_str = clean_str.replace(',', '')
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def extract_gstr3b_figures(text: str) -> dict:
    """
    Input: raw OCR text from a GSTR-3B PDF
    Extracts: declared taxable turnover, output tax paid, input tax credit (ITC) claimed
    """
    turnover = 0.0
    output_tax = 0.0
    itc_claimed = 0.0
    
    # 3.1 Outward taxable supplies
    turnover_match = re.search(r'(?:3\.1.*?supplies|declared\s*turnover).*?(?:₹|rs\.?)?\s*([\d\,\.]{4,})', text, re.IGNORECASE)
    if turnover_match:
        turnover = parse_indian_number(turnover_match.group(1))
        
    # Output tax paid
    tax_match = re.search(r'(?:output\s*tax|total\s*tax\s*liability|tax\s*payable).*?(?:₹|rs\.?)?\s*([\d\,\.]{3,})', text, re.IGNORECASE)
    if tax_match:
        output_tax = parse_indian_number(tax_match.group(1))
        
    # 4A ITC Available
    itc_match = re.search(r'(?:4\(?A\)?.*?itc\s*available|itc\s*claimed).*?(?:₹|rs\.?)?\s*([\d\,\.]{3,})', text, re.IGNORECASE)
    if itc_match:
        itc_claimed = parse_indian_number(itc_match.group(1))
        
    return {
        "turnover": turnover,
        "output_tax": output_tax,
        "itc_claimed": itc_claimed,
        "filing_period": "Current" # In a full system, extract date range
    }

def extract_gstr2a_figures(text: str) -> dict:
    """
    Input: raw OCR text from GSTR-2A PDF
    Extracts: supplier-reported ITC available to the company
    """
    itc_available = 0.0
    
    itc_match = re.search(r'(?:total\s*itc\s*available|itc\s*available\s*from\s*suppliers).*?(?:₹|rs\.?)?\s*([\d\,\.]{4,})', text, re.IGNORECASE)
    if itc_match:
        itc_available = parse_indian_number(itc_match.group(1))
        
    return {
        "itc_available_from_suppliers": itc_available,
        "supplier_count": 0, # Could be extracted if pattern is known
        "filing_period": "Current"
    }

def extract_bank_credits(text: str) -> dict:
    """
    Input: raw OCR text from bank statement
    Extracts total operational credits, excluding loans/OD sweeps.
    """
    total_credits = 0.0
    excluded_credits = 0.0
    
    exclusion_pattern = re.compile(r'(loan|od|overdraft|cc\s*limit|bank\s*transfer\s*in)', re.IGNORECASE)
    
    # Simple line-by-line parsing looking for Credit indicators
    lines = text.split('\n')
    for line in lines:
        if re.search(r'\b(cr|credit)\b', line, re.IGNORECASE):
            # Find all potential numbers
            numbers = re.findall(r'[\d\,\.]+', line)
            if numbers:
                # Find the largest sequential string of digits/commas (most likely the amount)
                amt_str = sorted(numbers, key=len, reverse=True)[0]
                amt = parse_indian_number(amt_str)
                
                # Exclude if keywords match
                if exclusion_pattern.search(line):
                    excluded_credits += amt
                else:
                    total_credits += amt
                    
    return {
        "total_credits": total_credits,
        "excluded_credits": excluded_credits,
        "period": "12 Months",
        "average_monthly_credit": total_credits / 12 if total_credits > 0 else 0
    }

def detect_circular_trading(bank_text: str) -> dict:
    """
    Scans bank statement for identical round-figure transactions repeating, 
    and matching debit/credit identical amounts.
    """
    patterns_found = []
    confidence = 0.0
    score_penalty = 0
    
    # 1. Round figure transactions (multiples of 1,00,000) repeating 3+ times
    round_numbers = []
    all_amounts = re.findall(r'([\d\,\.]+)', bank_text)
    vals = [parse_indian_number(a) for a in all_amounts]
    for v in vals:
        if v >= 100000 and v % 100000 == 0:
            round_numbers.append(v)
            
    from collections import Counter
    counts = Counter(round_numbers)
    for amt, count in counts.items():
        if count >= 3:
            patterns_found.append(f"Round figure {amt:,.2f} appears {count} times.")
            score_penalty += 5 * count  # Penalty applies per occurrence
            confidence = max(confidence, 0.8)
            
    # 2. Matching debits and credits in the same window
    # Without strict date parsing, we isolate Cr and Dr amounts on each line
    cr_amts = []
    dr_amts = []
    for line in bank_text.split('\n'):
        nums = re.findall(r'[\d\,\.]+', line)
        if nums:
            amt = parse_indian_number(max(nums, key=len))
            if re.search(r'\b(cr|credit)\b', line, re.IGNORECASE):
                cr_amts.append(amt)
            if re.search(r'\b(dr|debit)\b', line, re.IGNORECASE):
                dr_amts.append(amt)
                
    common_amts = set(cr_amts).intersection(set(dr_amts))
    for amt in common_amts:
        if amt > 10000: # Ignore tiny utility payments
            patterns_found.append(f"Matching debit and credit for amount {amt:,.2f} found within short window.")
            score_penalty += 5
            confidence = max(confidence, 0.6)
            
    # Do not hard cap penalty at 15 if there are multiple severe violations
    # Alternatively cap higher, e.g. 50
    score_penalty = min(score_penalty, 50)
    
    return {
        "circular_trading_detected": len(patterns_found) > 0,
        "suspicious_patterns": patterns_found,
        "confidence": confidence,
        "penalty": score_penalty
    }

def generate_gst_summary(reconciliation_result: dict) -> str:
    """
    Generates a 3-4 sentence LLM hook summarizing the finding.
    """
    score = reconciliation_result["reconciliation_score"]
    flags = reconciliation_result["flags"]
    rev_gap = reconciliation_result["revenue_gap_percent"]
    itc_gap = reconciliation_result["itc_gap_percent"]
    
    sentences = [f"The entity achieved a GST reconciliation score of {score}/100."]
    
    if abs(rev_gap) > 5:
        sentences.append(f"A revenue gap of {abs(rev_gap):.1f}% was observed between declared GSTR-3B turnover and operational bank credits.")
    
    if itc_gap > 0:
        sentences.append(f"ITC claimed exceeded supplier-reported availability by {itc_gap:.1f}%.")
        
    if any(f['type'] in ["CIRCULAR_TRADING_RISK", "SUSPICIOUS_TRANSACTIONS"] for f in flags):
        sentences.append("Suspicious transaction patterns indicative of potential circular trading or accommodation entries were detected.")
        
    if score >= 80:
        sentences.append("Overall GST compliance profile is satisfactory.")
    elif 60 <= score <= 79:
        sentences.append("GST compliance requires monitoring during the loan tenure.")
    else:
        sentences.append("Significant GST anomalies warrant enhanced due diligence before sanction.")
        
    return " ".join(sentences)

def reconcile(gstr3b: dict, gstr2a: dict, bank: dict, circular_trading: dict = None) -> dict:
    """
    Cross-verifies extracted data, sets high/medium flags, deducts penalties, and recommends action.
    """
    score = 100
    flags = []
    
    turnover = gstr3b.get('turnover', 0)
    bank_credits = bank.get('total_credits', 0)
    itc_claimed = gstr3b.get('itc_claimed', 0)
    itc_available = gstr2a.get('itc_available_from_suppliers', 0)
    output_tax = gstr3b.get('output_tax', 0)
    
    # 1. Revenue Gap (Absolute percentage)
    revenue_gap_percent = 0
    if bank_credits > 0:
        revenue_gap_percent = ((turnover - bank_credits) / bank_credits) * 100
        abs_gap = abs(revenue_gap_percent)
        if abs_gap > 15:
            flags.append({
                "type": "REVENUE_MISMATCH",
                "severity": "HIGH",
                "detail": f"Declared turnover ₹{turnover:,.2f} vs bank credits ₹{bank_credits:,.2f} \u2014 {abs_gap:.1f}% gap suggests possible mis-reporting or undocumented cash transactions.",
                "impact_on_score": -15
            })
            score -= 15
        elif abs_gap >= 5:
            flags.append({
                "type": "REVENUE_MISMATCH",
                "severity": "MEDIUM",
                "detail": f"Declared turnover ₹{turnover:,.2f} vs bank credits ₹{bank_credits:,.2f} \u2014 {abs_gap:.1f}% gap.",
                "impact_on_score": -7
            })
            score -= 7
            
    # 2. ITC Gap
    itc_gap_percent = 0
    if itc_available > 0:
        itc_gap_percent = ((itc_claimed - itc_available) / itc_available) * 100
        if itc_gap_percent > 20:
            flags.append({
                "type": "CIRCULAR_TRADING_RISK",
                "severity": "HIGH",
                "detail": f"ITC claimed (₹{itc_claimed:,.2f}) exceeds available from suppliers (₹{itc_available:,.2f}) by >20% ({itc_gap_percent:.1f}%).",
                "impact_on_score": -20
            })
            score -= 20
        elif itc_claimed > itc_available:
            flags.append({
                "type": "ITC_FRAUD_RISK",
                "severity": "HIGH",
                "detail": f"ITC claimed (₹{itc_claimed:,.2f}) exceeds available from suppliers (₹{itc_available:,.2f}).",
                "impact_on_score": -10
            })
            score -= 10
            
    # 3. Output Tax Consistency (Tax rate anomaly)
    if turnover > 0:
        tax_rate = (output_tax / turnover) * 100
        if not (5 <= tax_rate <= 30):
            flags.append({
                "type": "TAX_RATE_ANOMALY",
                "severity": "MEDIUM",
                "detail": f"Output tax implies effective rate of {tax_rate:.1f}%, outside standard 5%-30% range.",
                "impact_on_score": -8
            })
            score -= 8
            
    # 4. Circular trading penalty application
    ct_data = circular_trading or {}
    penalty = ct_data.get('penalty', 0)
    if penalty > 0:
        score -= penalty
        for p in ct_data.get('suspicious_patterns', []):
            flags.append({
                "type": "SUSPICIOUS_TRANSACTIONS",
                "severity": "HIGH",
                "detail": p,
                "impact_on_score": -5
            })

    score = max(0, int(score))

    has_high = any(f['severity'] == 'HIGH' for f in flags)
    has_medium = any(f['severity'] == 'MEDIUM' for f in flags)
    
    if score >= 75 and not has_high:
        recommendation = "PROCEED"
    elif score < 55 or has_high:
        recommendation = "FLAG_FOR_REVIEW"
    else:
        recommendation = "PROCEED_WITH_CAUTION"

    result = {
        "reconciliation_score": score,
        "revenue_gap_percent": round(revenue_gap_percent, 2) if bank_credits > 0 else 0,
        "itc_gap_percent": round(itc_gap_percent, 2) if itc_available > 0 else 0,
        "flags": flags,
        "circular_trading": ct_data,
        "recommendation": recommendation
    }
    
    result["summary_paragraph"] = generate_gst_summary(result)
    return result

if __name__ == "__main__":
    # Inline test
    gstr3b_mock = "3.1 Outward taxable supplies: Rs 1,45,00,000.00 \n Output tax: 2,00,000 \n 4(A) ITC Available: 5,60,000"
    gstr2a_mock = "Total ITC available from suppliers: 4,00,000"
    bank_mock = "12-05-2023 Invoice Payment 50,00,000 Cr \n 14-05-2023 Loan disbursal 9,00,000 Cr \n 15-05-2023 Payment 50,00,000 Dr \n 18-05-2023 Client funds 50,00,000 Cr \n 20-05-2023 Bank transfer IN OD 2,00,000 Cr \n 22-05-2023 Payment 50,00,000 Cr"
    
    dict_3b = extract_gstr3b_figures(gstr3b_mock)
    dict_2a = extract_gstr2a_figures(gstr2a_mock)
    dict_bank = extract_bank_credits(bank_mock)
    ct_results = detect_circular_trading(bank_mock)
    
    print("--- 3B Data ---", dict_3b)
    print("--- 2A Data ---", dict_2a)
    print("--- Bank Data ---", dict_bank)
    print("--- Circular Trading ---", ct_results)
    
    import json
    final_report = reconcile(dict_3b, dict_2a, dict_bank, circular_trading=ct_results)
    print("\n--- FINAL RECONCILIATION ---")
    print(json.dumps(final_report, indent=2))
