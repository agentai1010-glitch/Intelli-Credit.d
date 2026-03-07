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
    
    # Simple regex search across raw_text to find actual financial figures!
    text = str(raw_text).replace(',', '').lower()
    
    rev_match = re.search(r'revenue[^\d]*(\d+)', text)
    revenue = float(rev_match.group(1)) if rev_match else document_data.get("extracted_revenue", 0)
    
    exp_match = re.search(r'expense[^\d]*(\d+)', text)
    expenses = float(exp_match.group(1)) if exp_match else document_data.get("extracted_expenses", 0)
    
    if expenses > 0:
        feature_dict["revenue_expense_ratio"] = revenue / expenses
        
    assets_match = re.search(r'current assets[^\d]*(\d+)', text)
    current_assets = float(assets_match.group(1)) if assets_match else document_data.get("current_assets", 0)
    
    liab_match = re.search(r'current liabilit[^\d]*(\d+)', text)
    current_liabilities = float(liab_match.group(1)) if liab_match else document_data.get("current_liabilities", 0)
    
    feature_dict["working_capital"] = current_assets - current_liabilities
    
    debt_match = re.search(r'total debt[^\d]*(\d+)', text)
    debt = float(debt_match.group(1)) if debt_match else document_data.get("total_debt", 0)
    
    equity_match = re.search(r'total equity[^\d]*(\d+)', text)
    equity = float(equity_match.group(1)) if equity_match else document_data.get("total_equity", 0)
    
    if equity > 0:
        feature_dict["debt_equity_ratio"] = debt / equity
        
    # GST vs Bank match score (1.0 = perfect match, 0.0 = terrible match)
    # The reconciler already gives us a 0-100 score, map it directly!
    gst_score = document_data.get("gst_reconciliation_score")
    if gst_score is not None:
        feature_dict["gst_bank_match_score"] = float(gst_score)
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
