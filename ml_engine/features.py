import pandas as pd
import re
from typing import Dict, List

def extract_features(raw_text: str, document_data: Dict, entity_data: List[Dict]) -> pd.DataFrame:
    """
    Ingests cleaned raw_text from OCR and applies regex extraction for real financial figures.
    Computes basic financial ratios and other features.
    """
    feature_dict = {
        "revenue_expense_ratio": 1.0,
        "working_capital": 0.0,
        "debt_equity_ratio": 0.0,
        "gst_bank_match_score": 0.0,
        "legal_flag_count": 0,
        "sector_risk_flag": 0
    }
    
    # New feature definitions per user request
    text = str(raw_text).replace(',', '').lower()
    
    rev_match = re.search(r'revenue[^\d]*(\d+)', text)
    revenue = float(rev_match.group(1)) if rev_match else document_data.get("extracted_revenue", document_data.get("revenue", 0))
    
    ebitda_match = re.search(r'ebitda[^\d]*(\d+)', text)
    ebitda = float(ebitda_match.group(1)) if ebitda_match else document_data.get("extracted_expenses", document_data.get("ebitda", 0))
    
    if revenue > 0:
        feature_dict["revenue_expense_ratio"] = ebitda / revenue
        
    net_worth_match = re.search(r'net worth[^\d]*(\d+)', text)
    net_worth = float(net_worth_match.group(1)) if net_worth_match else document_data.get("net_worth", 0)
    
    debt_match = re.search(r'existing debt[^\d]*(\d+)', text)
    existing_debt = float(debt_match.group(1)) if debt_match else document_data.get("existing_debt", document_data.get("total_debt", 0))
    
    feature_dict["working_capital"] = net_worth - existing_debt
    
    if net_worth > 0:
        feature_dict["debt_equity_ratio"] = existing_debt / net_worth
    elif "debt_equity_ratio" in document_data:
        feature_dict["debt_equity_ratio"] = float(document_data.get("debt_equity_ratio", 0))
        
    # GST vs Bank match score (1.0 = perfect match, 0.0 = terrible match)
    # The reconciler already gives us a 0-100 score, map it directly!
    reconciliation_score = document_data.get("reconciliation_score", document_data.get("gst_reconciliation_score"))
    if reconciliation_score is not None:
        feature_dict["gst_bank_match_score"] = float(reconciliation_score) / 100.0
    else:
        # Fallback ratio if no recon score provided
        gst_turnover = document_data.get("gst_turnover", 0)
        bank_credits = document_data.get("bank_credits", 0)
        
        if max(gst_turnover, bank_credits) > 0:
            diff_pct = abs(gst_turnover - bank_credits) / max(gst_turnover, bank_credits)
            feature_dict["gst_bank_match_score"] = max(0.0, 1.0 - diff_pct)

    # Number of red flags from entities (e.g., LAW type entities, NPA mentions)
    red_flag_count = 0
    for ent in entity_data:
        if ent.get("type") in ["LAW"]:
            red_flag_count += 1
        text_check = ent.get("text", "").lower()
        if "npa" in text_check or "insolvency" in text_check or "default" in text_check:
            red_flag_count += 1
            
    feature_dict["legal_flag_count"] = red_flag_count
    
    # Sector risk flag (Example: 1 for high risk, 0 for normal)
    feature_dict["sector_risk_flag"] = document_data.get("sector_risk", 0)
    
    return pd.DataFrame([feature_dict])
